# DECISIONS — вопросы и решения по порту exteraGram → iOS (Swiftgram)

Здесь записаны вопросы и ответы. **Секреты сюда не пишем.**

Документация порта лежит в `docs/exteraios/`, а не в корневой `docs/`: там свои файлы Swiftgram, а отдельная папка не конфликтует с апстримом при ребейзе.
Секреты (`api_id`, `api_hash`) хранятся только в **GitHub Actions Secrets** репозитория порта (`TG_API_ID`, `TG_API_HASH`).
CI собирает из них конфиг сборки во временный файл, который не попадает в git.

Статусы: ⏳ ждёт ответа · ✅ решено · 🔁 отложен (задам, когда будут факты из кода) · 🤝 решение делегировано агенту

---

## Этап 0 — окружение и сборка

### Факты (проверено 24.11.2026)
- Агент работает на Windows 11 Pro 10.0.26100, Xcode и Bazel нет. Локальная сборка iOS невозможна.
- Аккаунт `gh` залогинен, права `repo` и `workflow` есть.
- `Swiftgram/Telegram-iOS@master`: в `versions.json` app 13.2.1, Xcode 27.1, macOS 27, Bazel 9.2.0. LICENSE нет (`license: null` в GitHub API).
- В апстриме есть `.github/workflows/build.yml` (только ручной запуск, `runs-on: macos-13`). Он собирает **неподписанную** IPA (`release_arm64`) с `build-system/fake-codesigning` и публикует её в Releases. Конфиг берёт из `build-system/appstore-configuration.json`, то есть с ключами официального Telegram. **Нам так нельзя**, нужен свой конфиг из секретов.
- `build-system/fake-codesigning/profiles/*.mobileprovision`: фейковые профили для `C67CF9S4VU.ph.telegra.Telegraph` (bundle ID и Team ID официального Telegram), срок действия истёк **2026-10-30**. Для нашего bundle ID нужны свои фейковые сертификат и профили (самоподписанные, к Apple отношения не имеют).
- В GitHub Actions есть образ `xcode-27` (preview, issue actions/runner-images#14404): macOS 27.0.1, **Xcode 27.1 по умолчанию** (есть ещё 27.0 и 27.2), симуляторы iOS 27.x. Это совпадает с `versions.json`, поэтому `--overrideXcodeVersion` не нужен.

### Вопросы блока A и п. 25

| # | Вопрос | Статус | Ответ / решение |
|---|--------|--------|-----------------|
| 0 | Где работаем | ✅ | Своего Mac нет. Сборка в GitHub Actions в открытом репозитории (раннер `xcode-27`) |
| 1 (A1) | Версии macOS / Xcode | ✅ | Раннер `xcode-27`: macOS 27, Xcode 27.1, совпадает с `versions.json` |
| 2 (A2) | `api_id` / `api_hash` | ⏳ | Пользователь даст позже. Хранить только в GitHub Secrets |
| 3 (A3) | `bundle_id` | ⏳ | Ответ на #3 относился к Pro (см. B11). Bundle ID спрошен повторно (вопрос #12) |
| 4 (A4) | `team_id` / тип аккаунта | ✅ | Установка через **Sideloadly** с **бесплатным Apple ID**. Подпись живёт 7 дней, лимит 10 App ID в неделю (у нас 7: приложение + 6 расширений), пушей нет |
| 5 (A5) | Способ подписи | ✅ | CI собирает IPA с фейковой подписью (свои самоподписанные сертификат и профили), Sideloadly переподписывает её на устройстве пользователя |
| 6 (A6) | Расширения | 🤝 | Все, кроме Watch: Share, NotificationService, NotificationContent, Widget, Intents, BroadcastUpload. Лишние можно убрать в Sideloadly при установке |
| 7 (A7) | `enable_siri` / `enable_icloud` / `aps_environment` | 🤝 | `enable_siri=false`, `enable_icloud=false`. Entitlements всё равно переписывает Sideloadly при подписи |
| 8 (A8) | Пуш-уведомления | ✅ (следствие #14) | Бесплатный Apple ID не даёт entitlement `aps-environment`, поэтому пушей не будет. Уведомления только пока приложение открыто или работает в фоне. Если перейдёте на платный аккаунт, вернусь к вопросу |
| 9 (A9) | Прочие поля конфига | 🤝 | `is_internal_build=false`, `is_appstore_build=false`, `appstore_id="0"` (так в шаблоне апстрима, значит «не в App Store»), `premium_iap_product_id=""`. `app_specific_url_scheme` выберу после ответа на #12: `tg` занят официальным Telegram |
| 10 (A10) | Версия и номер сборки | ✅ | A: версия как у Swiftgram (13.2.1). Номер сборки = число коммитов + `build_number_offset`, как в CI апстрима |
| 11 (п. 25) | Распространение | ✅ | Sideload через Sideloadly, App Store не нужен |

## Блок B

| # | Вопрос | Статус | Ответ / решение |
|---|--------|--------|-----------------|
| B11 | Swiftgram Pro и покупки | ✅ (пользователь) | **Открыть Pro-функции без покупки** (ответ пользователя «просто анлокнуть, это не запрещено»). Юридическую оценку агент не делает. На этапе 2 составлю список Pro-функций и отмечу те, что зависят от сервера Swiftgram |
| B12, B13 | `sg_config`, удалённые настройки и строки | ⏳ | Задам на этапе 2 |

## Блоки C, D

Будут заданы на этапе 2 (вопросы 14–24 промта).

## Вопросы этапа 0, второй раунд (24.11.2026)

| # | Вопрос | Статус | Ответ / решение |
|---|--------|--------|-----------------|
| 12 | `bundle_id` | ✅ / ⏳ | Вариант B: `com.itzchelove4ik.<имя>`, нужно имя приложения (вопрос #16) |
| 13 | Репозиторий порта | ✅ / ⏳ | **Публичный, не форк**, история Swiftgram + remote `upstream`. Имя — вопрос #16 |
| 14 | Apple ID для Sideloadly | ✅ | Бесплатный |
| 15 | Проверка этапа 0 | ✅ | CI собирает IPA, установку и вход проверяет пользователь на телефоне. Агент проверяет только, что сборка прошла |
| 16 | Имя приложения и репозитория | ✅ | **ExteraIOS** (выбор пользователя). Bundle ID `com.itzchelove4ik.exteraios`, репозиторий `ItzChelove4ik/ExteraIOS` (создан 24.11.2026, публичный, не форк), URL-схема `exteraios`, фейковый Team ID для самоподписанной сборки `EXTERAIOS1` |
| 17 | Название и `ADDITIONAL_TERMS.md` exteraGram, п. 2–3 | ✅ | Пользователь оставил «ExteraIOS» (24.11.2026). Условия запрещают использовать имя «exteraGram» как имя модифицированной версии и выдавать её за exteraGram. Подходит ли «ExteraIOS» — решает пользователь |

## Ключи: что нужно для iOS (проверено 24.11.2026)

Пользователь заметил, что exteraGram нужны не только `api_id`/`api_hash`. Факты:
- `exteraGram/README.md` и `TMessagesProj/build.gradle`: файл `API_KEYS` содержит `APP_ID`, `APP_HASH`, `MAPS_V2_API` и три пароля keystore.
  - `MAPS_V2_API` — ключ Google Maps для `play-services-maps`. **На iOS он не нужен**: карты в Telegram-iOS работают на Apple MapKit (`submodules/LocationUI/Sources/LocationMapNode.swift`: `import MapKit`), а MapKit ключа не требует.
  - Пароли keystore нужны только для подписи Android-APK, на iOS не нужны.
- `BuildVars.java`: `SAFETYNET_KEY = ""` (Android, выключен), остальное — публичные ссылки, не ключи.
- Ключи для AI (Gemini, OpenAI, OpenRouter, Perplexity) пользователь вводит в интерфейсе приложения, при сборке они не нужны.
- Что ещё может понадобиться (вопросы этапа 2, задам там): `sg_config` Swiftgram (B12), Firebase (C15, Android-only `google-services.json`, чужой брать нельзя), ключ P-256 для OTA SDK (C18), URL своего каталога плагинов (C17).
- **Итог на этапе 0:** для сборки нужны только `api_id` и `api_hash`.

## Этап 0 — как устроена сборка (24.11.2026)

- Локальные копии: `D:\ExteraIOS\swiftgram` (этот репозиторий, на C: не хватает места) и `D:\ExteraIOS\extera-android` (exteraGram `b4d852f4`, только для справки, shallow-клон).
- Remotes: `origin` = `ItzChelove4ik/ExteraIOS`, `upstream` = `Swiftgram/Telegram-iOS` (база `b460f1d894`, 13.2.1).
- Ветки: `master` — апстрим и смёрженные этапы, `exteraios/stage-N` — работа по этапам.
- CI: `.github/workflows/exteraios-build.yml` (раннер `xcode-27`). Запускается при пуше в `master` и `exteraios/**` или вручную, результат — IPA в артефактах запуска.
  Апстримный `.github/workflows/build.yml` не трогаем (запускается только вручную).
- Подпись: `build-system/exteraios/generate_fake_codesigning.py` при каждом запуске генерирует новую самоподписанную пару ключей и 9 профилей для `com.itzchelove4ik.exteraios` / `EXTERAIOS1`. Структуру entitlements берёт из апстримных профилей, все идентификаторы заменяет. Ключи в git не попадают.
- Конфиг сборки собирается в `$RUNNER_TEMP` из секретов `TG_API_ID` / `TG_API_HASH`. В git его нет.
- `sg_config` пустой: так ведёт себя немодифицированный Swiftgram, и приложение по умолчанию ходит на серверы Swiftgram (`api.swiftgram.app` и др.). Решение — вопрос B12, этап 2.
