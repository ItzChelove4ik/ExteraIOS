#!/usr/bin/env python3
# MARK: EXTERA
#
# Generates a self-signed "fake" codesigning directory (certs/ + profiles/) for an
# arbitrary bundle ID, in the layout that `Make.py --codesigningInformationPath` expects.
#
# Why: the upstream `build-system/fake-codesigning` profiles are bound to the official
# Telegram bundle ID / Team ID and have expired. ExteraIOS is distributed via sideloading
# (Sideloadly re-signs the IPA with the user's own Apple ID), so the build only needs a
# structurally valid signature. Nothing here is an Apple-issued certificate.
#
# The upstream fake profiles are used only as a template for the entitlement *structure*
# (which keys each extension needs); every identifier, the certificate and the dates are
# replaced. A fresh key pair is generated on every run and never stored in git.

import argparse
import datetime
import os
import plistlib
import subprocess
import sys
import tempfile
import uuid

UPSTREAM_TEAM_ID = 'C67CF9S4VU'
UPSTREAM_BUNDLE_ID = 'ph.telegra.Telegraph'
UPSTREAM_TEAM_NAME = 'Telegram FZ-LLC'


def run(args, **kwargs):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if result.returncode != 0:
        sys.stderr.write(result.stderr.decode('utf-8', errors='replace'))
        raise SystemExit('command failed: {}'.format(' '.join(args)))
    return result.stdout


def extract_plist(profile_path):
    data = open(profile_path, 'rb').read()
    start = data.find(b'<?xml')
    end = data.find(b'</plist>')
    if start < 0 or end < 0:
        raise SystemExit('no plist in {}'.format(profile_path))
    return plistlib.loads(data[start:end + len(b'</plist>')])


def replace_identifiers(value, team_id, bundle_id, team_name):
    if isinstance(value, str):
        return value.replace(UPSTREAM_BUNDLE_ID, bundle_id).replace(UPSTREAM_TEAM_ID, team_id).replace(UPSTREAM_TEAM_NAME, team_name)
    if isinstance(value, list):
        return [replace_identifiers(item, team_id, bundle_id, team_name) for item in value]
    if isinstance(value, dict):
        return {replace_identifiers(k, team_id, bundle_id, team_name): replace_identifiers(v, team_id, bundle_id, team_name) for k, v in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle-id', required=True)
    parser.add_argument('--team-id', required=True)
    parser.add_argument('--team-name', default='ExteraIOS Fake Signing')
    parser.add_argument('--template', required=True, help='Upstream fake-codesigning directory (profiles/ used as entitlement template)')
    parser.add_argument('--output', required=True)
    parser.add_argument('--openssl', default='openssl')
    # macOS 27 `security import` rejects PKCS#12 files with an empty password ("MAC verification
    # failed") and the OpenSSL 3 default algorithms; a password-protected `-legacy` file imports.
    # This is why the upstream ImportCertificates.py (which passes -P '') is not used for it.
    parser.add_argument('--p12-password', default='exteraios-fake')
    parser.add_argument('--aps-environment', default='development')
    args = parser.parse_args()

    if len(args.team_id) != 10 or not args.team_id.isalnum() or args.team_id.upper() != args.team_id:
        raise SystemExit('team id must be 10 uppercase alphanumeric characters')

    certs_dir = os.path.join(args.output, 'certs')
    profiles_dir = os.path.join(args.output, 'profiles')
    os.makedirs(certs_dir, exist_ok=True)
    os.makedirs(profiles_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as work:
        key_path = os.path.join(work, 'key.pem')
        cert_path = os.path.join(work, 'cert.pem')
        subject = '/CN=Apple Distribution: {} ({})/OU=SELFSIGNED/C=US'.format(args.team_name, args.team_id)
        run([args.openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256',
             '-days', '3650', '-subj', subject,
             '-addext', 'keyUsage=critical,digitalSignature',
             '-addext', 'extendedKeyUsage=critical,codeSigning',
             '-keyout', key_path, '-out', cert_path])
        cert_der = run([args.openssl, 'x509', '-in', cert_path, '-outform', 'der'])
        open(os.path.join(certs_dir, 'Public.cer'), 'wb').write(cert_der)
        version = run([args.openssl, 'version']).decode()
        legacy = ['-legacy'] if version.startswith('OpenSSL') and not version.startswith('OpenSSL 1.') else []
        run([args.openssl, 'pkcs12', '-export'] + legacy + ['-inkey', key_path, '-in', cert_path,
             '-passout', 'pass:' + args.p12_password, '-out', os.path.join(certs_dir, 'SelfSigned.p12')])

        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None)
        template_dir = os.path.join(args.template, 'profiles')
        count = 0
        for file_name in sorted(os.listdir(template_dir)):
            if not file_name.endswith('.mobileprovision'):
                continue
            profile = extract_plist(os.path.join(template_dir, file_name))
            profile = replace_identifiers(profile, args.team_id, args.bundle_id, args.team_name)
            profile['DeveloperCertificates'] = [cert_der]
            profile['UUID'] = str(uuid.uuid4())
            profile['CreationDate'] = now
            profile['ExpirationDate'] = now + datetime.timedelta(days=3650)
            profile['TimeToLive'] = 3650
            profile['Name'] = 'ExteraIOS fake {}'.format(file_name[:-len('.mobileprovision')])
            profile.pop('DER-Encoded-Profile', None)
            entitlements = profile['Entitlements']
            if 'aps-environment' in entitlements:
                entitlements['aps-environment'] = args.aps_environment
            app_id = entitlements['application-identifier']
            if not app_id.startswith(args.team_id + '.' + args.bundle_id):
                raise SystemExit('unexpected application-identifier {} in {}'.format(app_id, file_name))

            plist_path = os.path.join(work, file_name + '.plist')
            with open(plist_path, 'wb') as f:
                plistlib.dump(profile, f)
            run([args.openssl, 'cms', '-sign', '-binary', '-nodetach', '-outform', 'DER',
                 '-signer', cert_path, '-inkey', key_path,
                 '-in', plist_path, '-out', os.path.join(profiles_dir, file_name)])
            print('profile {} -> {}'.format(file_name, app_id))
            count += 1

    if count == 0:
        raise SystemExit('no template profiles found in {}'.format(template_dir))
    print('generated {} profiles in {}'.format(count, profiles_dir))


if __name__ == '__main__':
    main()
