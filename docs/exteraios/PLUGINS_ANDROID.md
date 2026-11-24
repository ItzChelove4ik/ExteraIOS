# Система плагинов exteraGram (Android): полный разбор

Источник: `exteraSquad/exteraGram@b4d852f4` (13.2.2), только чтение.
- Python SDK: `plugins-pysdk/src/`, 33 файла, 13 931 строка.
- Kotlin-часть: `TMessagesProj/src/full/java/com/exteragram/messenger/plugins/`, 83 файла, 22 535 строк.

API ниже не описан по памяти. Раздел 9 сгенерирован из AST исходников (`ast.parse`, без выполнения). Разделы 1–8 составлены по коду, у каждого утверждения указан файл.

## 1. Архитектура

- **Рантайм**: CPython 3.11 внутри приложения через **Chaquopy**. Есть только в версии `full`; в `lite` плагинов нет.
- **SDK** поставляется в APK как `plugins_pysdk/sdk-<abi>.zip`: модули скомпилированы в `.pyc` без исходников (`-OO`), рядом лежит `v.txt` с `<версия>|<1 бета / 0 стабильная>`. При первом запуске архив распаковывается в каталог приложения и добавляется в `sys.path` (`plugins-pysdk/README.md`). **Байткод привязан к Python 3.11**, сборщик отказывается работать на другой версии.
- **Движок**: `elyxcore/_plugin_engine.py` реализует Kotlin-интерфейс `PluginsController.PluginsEngine` через Chaquopy `@joverride` (README, раздел «Changing the engine interface»). Методы интерфейса (`PluginsController.kt`):
  - управление: `init`, `shutdown`, `isPlugin`, `parsePluginMetadata`, `setPluginEnabled`, `deletePlugin`, `getPluginPath`, `sharePlugin`, `openInExternalApp`, `checkDevServer`;
  - настройки: `loadPluginSettings`, `get/setPluginSetting`, `clearPluginSettings`, `getAllPluginSettings`, `openPluginSettings`, `openPluginSetting(linkAlias)`;
  - события и хуки: `executeOnAppEvent`, `executePreRequestHook`, `executePostRequestHook`, `executeUpdateHook`, `executeUpdatesHook`, `executeSendMessageHook`;
  - установка: `showInstallDialog`, `loadPluginFromFile`.
- **Типы в хуках**: `TLObject`/`TLRPC.*` и `SendMessagesHelper.SendMessageParams` — это **Java-объекты**, которые Python получает через Chaquopy. Плагины читают и меняют их поля напрямую (`request.message`, `params.peer` и т. д.).
- **Прямой доступ к Java/Android**: SDK и плагины импортируют `java.*`, `android.*`, `org.telegram.*`, `com.exteragram.*` (у каждого модуля зависимости перечислены в разделе 9).

## 2. Формат плагина и метаданные

- `.plugin` — один файл с **исходником Python**. Метаданные — переменные модуля (`extera_utils/metadata_parser.py`): `__id__`, `__name__`, `__description__`, `__author__`, `__version__`, `__icon__`, `__min_version__`, `__requirements__`, `__app_version__`, `__sdk_version__`. В Python они приходят как `PluginMetadata(id, name, description, author, version, icon, min_version, requirements)` (`base_plugin.py`).
- `.elyx` — пакет плагина для движка ElyxCore с поддержкой зависимостей: `wheel_names` в метаданных становятся `bundledPackages` при установке (`elyxcore/_install.py:240`). Зависимости ставит `pip/PipController.kt` (реестр установленных пакетов, `PREINSTALLED_PACKAGES`, `installDependencies`) с проверкой конфликтов модулей с SDK (`PythonPluginsEngine.kt:772–784`).
- Плагин — класс-наследник `BasePlugin`.

## 3. Жизненный цикл

| Этап | Что происходит | Где |
|---|---|---|
| Запуск приложения | `PluginsController.init(startWithSafeMode)`: проверка нативного падения (`NativeCrashHandler`), разбор флагов `had_crash` / `crashed_plugin_id`, затем загрузка плагинов | `PluginsController.kt:162–206` |
| Загрузка плагина | `on_plugin_load()` | `BasePlugin` |
| Выгрузка | `on_plugin_unload()`, функции из `register_cleanup()`, событие `stop_event` | `BasePlugin` |
| События приложения | `on_app_event(AppEvent.START / STOP / PAUSE / RESUME)` | `PluginsConstants.APP_*` |
| Настройки | `create_settings()` возвращает список контролов | раздел 5 |

## 4. Хуки

### 4.1. Высокоуровневые (TL и отправка) — переносимая часть
- Регистрация: `add_hook(name, match_substring=False, priority=0)` — по имени TL-запроса или апдейта; `add_on_send_message_hook(priority)`; `remove_hook(name)`.
- Обработчики `BasePlugin`:
  - `pre_request_hook(request_name, account, request)` — перед отправкой TL-запроса;
  - `post_request_hook(request_name, account, response, error)` — после ответа;
  - `on_update_hook(update_name, account, update)` и `on_updates_hook(container_name, account, updates)` — входящие апдейты;
  - `on_send_message_hook(account, params)` — отправка сообщения (`SendMessageParams`).
- Возвращают `HookResult(strategy, request, response, update, updates, error, params)`, стратегии — `HookStrategy`: `DEFAULT` (ничего не менять), `MODIFY` (заменить объект), `CANCEL` (отменить), `MODIFY_FINAL` (заменить и не звать хуки следующих плагинов).
- Хуки файлов и интентов: `add_file_hook(FilesController.FileInfo)`, `remove_file_hook`, `add_intent_hook(IntentsManager.HandlerInfo, IntentHookType.BEFORE/AFTER)`, `remove_intent_hook`.

### 4.2. Хукинг методов ART (Xposed-подобный) — специфично для Android
- `hook_method(member, xposed_hook | before= / after=, priority)`, `hook_all_methods(class, name, …)`, `hook_all_constructors(class, …)`, `unhook_method(unhook)`. Обработчики — `MethodHook.before_hooked_method(param)` / `after_hooked_method(param)` и `MethodReplacement.replace_hooked_method(param)`, где `param` — `XC_MethodHook.MethodHookParam`. Реализовано на LSPlant и shadowhook (`xposed/PyMethodHook.kt`, `PyMethodReplacement.kt`, `hooks/XposedHookRecord.kt`).
- Частичные хуки внутри тела метода: `hook_call_site(in_method, callee, cb)`, `hook_field_read(in_method, field, cb)`, `hook_field_write`, `hook_string_constant(in_method, text, cb)`, `hook_return_value(in_method, cb)`, `unhook_partial(handle)`. В колбэк приходит `PartialChain` (`this_object`, `caller`, `args`, `arg(i)`, `proceed(*args)`, `throw_to_caller`) (`hooks/PartialHookRecord.kt`).
- Фильтры `HookFilter`: `RESULT_IS_NULL/TRUE/FALSE/NOT_NULL`, `ResultIsInstanceOf`, `ResultEqual/NotEqual`, `ArgumentIsNull/True/False/NotNull(i)`, `ArgumentIsInstanceOf`, `ArgumentEqual/NotEqual`, `Condition(mvel_expression)`, `Or(*filters)`; декораторы `hook_filters(*filters)` и `fn_hook_filters(field)` (`hooks/HookFilter.kt`).
- Цели указываются **Java-классами Android-версии** (`org.telegram.ui.Cells.DialogCell` и т. п.), найденными через `find_class` / reflection.

## 5. Настройки плагина (`create_settings`)

Типы из `PluginsConstants.Settings` и `ui/settings.py`: `switch`, `input`, `selector`, `header`, `divider`, `text`, `edit_text`, `custom`. Общие поля: `key`, `text`, `subtext`, `icon`, `accent`, `red`, `default`, `items` (для selector), `hint`, `multiline`, `max_length`, `mask`, `on_change`, `on_click`, `on_long_click`, `link_alias` (глубокая ссылка на пункт), `create_sub_fragment` (вложенный экран). У `custom` есть `view` / `item` / `factory` / `factory_args`.
Хранение: `get_setting` / `set_setting(reload_settings)` / `export_settings` / `import_settings`. С недавней версии значения хранятся в JSON, а не в SharedPreferences: есть миграция (`PythonPluginsEngine.kt:515`).
UI: `ui/PluginSettingsActivity.kt`, перевод настроек — `PluginSettingsTranslation.kt`.

## 6. Пункты меню

`add_menu_item(MenuItemData(menu_type, text, on_click, item_id, icon, subtext, condition, priority, on_long_click))` и `remove_menu_item(item_id)`. Типы меню: `message_context_menu`, `drawer_menu`, `main_menu`, `chat_action_menu`, `profile_action_menu`. `condition` — MVEL-выражение. В `on_click` приходит словарь контекста (`utils/MenuContextBuilder.kt`).

## 7. Вспомогательные модули SDK (подробно — раздел 9)

`client_utils` (отправка запросов и сообщений, доступ к контроллерам аккаунта), `android_utils` (`run_on_ui_thread`, `log`, `copy_to_clipboard`, `OnClickListener`), `ui.alert`, `ui.bulletin`, `ui.settings`, `file_utils`, `markdown_utils` (`RawEntity`, `ParsedMessage`), `log_utils`, `intents`, `hook_utils`, `plugin_settings`, `dev_server`.

## 8. Установка, каталог, обновления, безопасность

- **Установка**: из файла или документа в чате (`isPlugin(file, messageObject)`). Перед установкой показывается `InstallPluginBottomSheet`: метаданные, требования (`PluginRequirementsView`), результат анализатора. Для источников вне каталога нужно включить `pluginsUnknownSources` (`UnknownSourcesBottomSheet`).
- **Каталог**: `catalog/PluginCatalogController.kt` с локальной БД Room (`catalog/db/*`) и категориями. Git-репозитории подключаются через `GitPluginRepository.kt`: файлы с GitHub берутся с `raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>`, запасной вариант — `cdn.jsdelivr.net/gh/...`.
- **OTA-обновления SDK** приходят **документами из Telegram-канала обновлений** (`updates/TelegramUpdateSource.kt` ищет документы через `searchMessages` и скачивает их через `FileLoader`). Ставится только подписанное: подписывается строка `extera-pysdk|<version>|<abi>|<sha256 архива>` ключом **P-256**, алгоритм `SHA256withECDSA` (`updates/SignedArtifact.kt`). Публичный ключ зашит в `utils/SdkSignature.kt` (ровно один); приватного ключа в репозитории нет. В сообщении можно ограничить версии приложения (`app_version>=…`, `app_version_code`).
- **Анализатор**: `analyzer/*` — обёртка над закрытой нативной библиотекой (`AnalyzerNative.kt`), которая обновляется отдельно (`AnalyzerUpdater.kt`) и проверяется по хешам (`AnalyzerHashes.kt`). Отчёт показывается в `PluginAnalysisReportSheet`.
- **Safe mode**: если плагин уронил приложение, при следующем запуске он выключается (`crashed_plugin_id`) и включается `pluginsSafeMode`, пока safe mode включён, плагины нельзя включить (`"Plugins cannot be enabled while safe mode is active"`), SDK восстанавливается из APK с удалением OTA-версии, проверка обновлений SDK не запускается (`PluginsController.kt:191–206`, `PythonPluginsEngine.kt:110, 240, 303–309, 490`, `SafeModeBottomSheet`). В SDK есть `SafeModeImporter` (`_sdk_version.py`).
- **Watchdog**: `utils/PluginsWatchdog.kt` отслеживает, какой плагин сейчас выполняется в каждом потоке. Если выполнение длится **больше 5 секунд**, плагин помечается «не отвечает» и показывается диалог: отключить плагин, удалить его или перезапустить приложение.
- **Dev server**: `dev_server.py` / `elyxcore/_dev_server.py` — сокет-сервер для заливки плагина с компьютера во время разработки, включается `pluginsDevMode`.
- **Нативные падения**: `utils/NativeCrashHandler.kt`.

## 9. Публичный API SDK (сгенерировано из AST)

Колонка «Описание» — первая фраза docstring, если она есть (у большинства функций docstring нет). Внутренние модули (имя начинается с `_`) приведены для полноты.

### `_sdk_version.py` (246 строк) — внутренний модуль

Java/Android-зависимости: `com.chaquo.python`, `com.exteragram.messenger`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.xposed`, `com.exteragram.messenger.utils`, `java.lang`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `SafeModeImporter` | `(importlib.abc.MetaPathFinder, importlib.abc.Loader)` |  |
| const | `SafeModeImporter.IS_OLD_VERSION` | `= False` |  |
| const | `SafeModeImporter.I` | `= False` |  |
| const | `SafeModeImporter.E` | `= False` |  |
| method | `SafeModeImporter.find_spec` | `(self, fullname, path, target=...)` |  |
| method | `SafeModeImporter.c` | `(cls)` |  |
| const | `Z` | `= SafeModeImporter()` |  |
| class | `X` | `` |  |
| const | `X.BUILD_VERSION` | `= None` |  |
| func | `check_safemode` | `()` |  |
| func | `setup_hooks` | `()` |  |

### `android_utils.py` (143 строк)

Java/Android-зависимости: `android.view`, `com.android.dx`, `com.chaquo.python`, `com.exteragram.messenger.plugins.utils`, `com.exteragram.messenger.utils`, `java`, `java.lang`, `java.lang.reflect`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `OnClickListener` | `(dynamic_proxy(View.OnClickListener))` |  |
| method | `OnClickListener.__init__` | `(self, fn: callable)` |  |
| method | `OnClickListener.onClick` | `(self, _view)` |  |
| class | `OnLongClickListener` | `(dynamic_proxy(View.OnLongClickListener))` |  |
| method | `OnLongClickListener.__init__` | `(self, fn: callable)` |  |
| method | `OnLongClickListener.onLongClick` | `(self, _view)` |  |
| func | `run_on_ui_thread` | `(func: callable, delay=0)` |  |
| func | `log` | `(data: Any)` |  |
| func | `copy_to_clipboard` | `(text: str)` |  |
| func | `R` | `(fn)` |  |

### `base_plugin.py` (1101 строк)

Java/Android-зависимости: `com.exteragram.hook`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.hooks`, `com.exteragram.messenger.plugins.xposed`, `java`, `java.lang`, `java.lang.reflect`, `java.util`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `PluginMetadata` | `` |  |
| field | `PluginMetadata.id` | `: str` |  |
| field | `PluginMetadata.name` | `: str` |  |
| field | `PluginMetadata.description` | `: str` |  |
| field | `PluginMetadata.author` | `: str` |  |
| field | `PluginMetadata.version` | `: str` |  |
| field | `PluginMetadata.icon` | `: str` |  |
| field | `PluginMetadata.min_version` | `: str` |  |
| field | `PluginMetadata.requirements` | `: List[str]` |  |
| class | `HookStrategy` | `(Enum)` |  |
| const | `HookStrategy.CANCEL` | `= PluginsConstants.Strategy.CANCEL` |  |
| const | `HookStrategy.MODIFY` | `= PluginsConstants.Strategy.MODIFY` |  |
| const | `HookStrategy.DEFAULT` | `= PluginsConstants.Strategy.DEFAULT` |  |
| const | `HookStrategy.MODIFY_FINAL` | `= PluginsConstants.Strategy.MODIFY_FINAL` |  |
| class | `IntentHookType` | `(Enum)` |  |
| const | `IntentHookType.BEFORE` | `= 0` |  |
| const | `IntentHookType.AFTER` | `= 1` |  |
| class | `HookResult` | `` |  |
| field | `HookResult.strategy` | `: HookStrategy = HookStrategy.DEFAULT` |  |
| field | `HookResult.request` | `: Any = None` |  |
| field | `HookResult.response` | `: Any = None` |  |
| field | `HookResult.update` | `: Any = None` |  |
| field | `HookResult.updates` | `: Any = None` |  |
| field | `HookResult.error` | `: Any = None` |  |
| field | `HookResult.params` | `: Any = None` |  |
| class | `PluginError` | `(Exception)` |  |
| field | `PluginError.plugin_id` | `: Optional[str]` |  |
| method | `PluginError.__init__` | `(self, message: str, plugin_id: Optional[str]=None)` |  |
| class | `XposedHook` | `(ABC)` |  |
| class | `MethodReplacement` | `(XposedHook)` |  |
| method | `MethodReplacement.replace_hooked_method` | `(self, param: XC_MethodHook.MethodHookParam)` |  |
| class | `MethodHook` | `(XposedHook)` |  |
| method | `MethodHook.before_hooked_method` | `(self, param: XC_MethodHook.MethodHookParam)` |  |
| method | `MethodHook.after_hooked_method` | `(self, param: XC_MethodHook.MethodHookParam)` |  |
| class | `PartialChain` | `` | One interception of a partial hook. |
| method | `PartialChain.__init__` | `(self, chain, param_types)` |  |
| method | `PartialChain.this_object` | `(self)` |  |
| method | `PartialChain.caller` | `(self)` |  |
| method | `PartialChain.args` | `(self)` |  |
| method | `PartialChain.arg` | `(self, index: int)` |  |
| method | `PartialChain.proceed` | `(self, *args)` |  |
| method | `PartialChain.throw_to_caller` | `(self, throwable)` |  |
| func | `fn_hook_filters` | `(field_name: str)` |  |
| class | `BaseHook` | `(MethodHook)` |  |
| method | `BaseHook.__init__` | `(self, plugin: Optional['BasePlugin']=None, *, before: Optional[Callable]=None, after: Optional[Callable]=None, before_filters: Optional[List[Any]]=None, aft...` |  |
| method | `BaseHook.before_hooked_method` | `(self, param)` |  |
| method | `BaseHook.after_hooked_method` | `(self, param)` |  |
| class | `AppEvent` | `(Enum)` |  |
| const | `AppEvent.START` | `= PluginsConstants.APP_START` |  |
| const | `AppEvent.STOP` | `= PluginsConstants.APP_STOP` |  |
| const | `AppEvent.PAUSE` | `= PluginsConstants.APP_PAUSE` |  |
| const | `AppEvent.RESUME` | `= PluginsConstants.APP_RESUME` |  |
| class | `MenuItemType` | `(Enum)` |  |
| const | `MenuItemType.MESSAGE_CONTEXT_MENU` | `= PluginsConstants.MenuItemTypes.MESSAGE_CONTEXT_MENU` |  |
| const | `MenuItemType.DRAWER_MENU` | `= PluginsConstants.MenuItemTypes.DRAWER_MENU` |  |
| const | `MenuItemType.MAIN_MENU` | `= PluginsConstants.MenuItemTypes.MAIN_MENU` |  |
| const | `MenuItemType.CHAT_ACTION_MENU` | `= PluginsConstants.MenuItemTypes.CHAT_ACTION_MENU` |  |
| const | `MenuItemType.PROFILE_ACTION_MENU` | `= PluginsConstants.MenuItemTypes.PROFILE_ACTION_MENU` |  |
| class | `MenuItemData` | `` |  |
| field | `MenuItemData.menu_type` | `: MenuItemType` |  |
| field | `MenuItemData.text` | `: str` |  |
| field | `MenuItemData.on_click` | `: Callable[[Dict[str, Any]], None]` |  |
| field | `MenuItemData.item_id` | `: Optional[str] = None` |  |
| field | `MenuItemData.icon` | `: Optional[str] = None` |  |
| field | `MenuItemData.subtext` | `: Optional[str] = None` |  |
| field | `MenuItemData.condition` | `: Optional[str] = None` |  |
| field | `MenuItemData.priority` | `: int = 0` |  |
| field | `MenuItemData.on_long_click` | `: Optional[Callable[[Dict[str, Any]], None]] = None` |  |
| class | `HookFilterData` | `` |  |
| field | `HookFilterData.filter_type` | `: str` |  |
| field | `HookFilterData.arg_index` | `: Optional[int] = None` |  |
| field | `HookFilterData.or_filters` | `: Optional[Any] = None` |  |
| field | `HookFilterData.mvel_expression` | `: Optional[str] = None` |  |
| field | `HookFilterData.instance_of` | `: Optional[Any] = None` |  |
| field | `HookFilterData.object` | `: Any = None` |  |
| method | `HookFilterData.to_java_filter` | `(self)` |  |
| class | `HookFilter` | `(Enum)` |  |
| const | `HookFilter.RESULT_IS_NULL` | `= PluginsConstants.HookFilterTypes.RESULT_IS_NULL` |  |
| const | `HookFilter.RESULT_IS_TRUE` | `= PluginsConstants.HookFilterTypes.RESULT_IS_TRUE` |  |
| const | `HookFilter.RESULT_IS_FALSE` | `= PluginsConstants.HookFilterTypes.RESULT_IS_FALSE` |  |
| const | `HookFilter.RESULT_NOT_NULL` | `= PluginsConstants.HookFilterTypes.RESULT_NOT_NULL` |  |
| method | `HookFilter.filter_data` | `(self)` |  |
| method | `HookFilter.ResultIsInstanceOf` | `(clazz)` |  |
| method | `HookFilter.ResultEqual` | `(value)` |  |
| method | `HookFilter.ResultNotEqual` | `(value)` |  |
| method | `HookFilter.ArgumentIsNull` | `(index: int)` |  |
| method | `HookFilter.ArgumentIsTrue` | `(index: int)` |  |
| method | `HookFilter.ArgumentIsFalse` | `(index: int)` |  |
| method | `HookFilter.ArgumentNotNull` | `(index: int)` |  |
| method | `HookFilter.ArgumentIsInstanceOf` | `(index: int, clazz)` |  |
| method | `HookFilter.ArgumentEqual` | `(index: int, value)` |  |
| method | `HookFilter.ArgumentNotEqual` | `(index: int, value)` |  |
| method | `HookFilter.Condition` | `(condition: str, object: Any=None)` |  |
| method | `HookFilter.Or` | `(*filters)` |  |
| func | `hook_filters` | `(*filters)` |  |
| class | `BasePlugin` | `` |  |
| method | `BasePlugin.__init__` | `(self)` |  |
| method | `BasePlugin.stop_event` | `(self)` |  |
| method | `BasePlugin.register_cleanup` | `(self, cleanup)` |  |
| method | `BasePlugin.on_plugin_load` | `(self)` |  |
| method | `BasePlugin.on_plugin_unload` | `(self)` |  |
| method | `BasePlugin.create_settings` | `(self)` |  |
| method | `BasePlugin.on_app_event` | `(self, event_type: AppEvent)` |  |
| method | `BasePlugin.pre_request_hook` | `(self, request_name: str, account: int, request: Any)` |  |
| method | `BasePlugin.post_request_hook` | `(self, request_name: str, account: int, response: Any, error: Any)` |  |
| method | `BasePlugin.on_update_hook` | `(self, update_name: str, account: int, update: Any)` |  |
| method | `BasePlugin.on_updates_hook` | `(self, container_name: str, account: int, updates: Any)` |  |
| method | `BasePlugin.on_send_message_hook` | `(self, account: int, params: Any)` |  |
| method | `BasePlugin.add_hook` | `(self, name: str, match_substring: bool=False, priority: int=0)` |  |
| method | `BasePlugin.add_on_send_message_hook` | `(self, priority: int=0)` |  |
| method | `BasePlugin.remove_hook` | `(self, name: str)` |  |
| method | `BasePlugin.add_file_hook` | `(self, file_info: FilesController.FileInfo)` |  |
| method | `BasePlugin.remove_file_hook` | `(self, ext, secret)` |  |
| method | `BasePlugin.add_intent_hook` | `(self, info: IntentsManager.HandlerInfo, type: IntentHookType)` |  |
| method | `BasePlugin.remove_intent_hook` | `(self, handler_id: Union[IntentsManager.HandlerHandle, str])` |  |
| method | `BasePlugin.get_setting` | `(self, key: str, default: Any=None)` |  |
| method | `BasePlugin.set_setting` | `(self, key: str, value: Any, reload_settings: bool=False)` |  |
| method | `BasePlugin.export_settings` | `(self)` |  |
| method | `BasePlugin.import_settings` | `(self, settings: dict, reload_settings: bool=True)` |  |
| method | `BasePlugin.hook_method` | `(self, method_or_constructor: Member, xposed_hook: Optional[Any]=None, priority: Optional[int]=None, *, before: Optional[Callable]=None, after: Optional[Call...` |  |
| method | `BasePlugin.hook_all_methods` | `(self, hook_class: Class, method_name: str, xposed_hook: Optional[Any]=None, priority: Optional[int]=None, *, before: Optional[Callable]=None, after: Optiona...` |  |
| method | `BasePlugin.hook_all_constructors` | `(self, hook_class: Class, xposed_hook: Optional[Any]=None, priority: Optional[int]=None, *, before: Optional[Callable]=None, after: Optional[Callable]=None, ...` |  |
| method | `BasePlugin.unhook_method` | `(self, unhook: XC_MethodHook.Unhook)` |  |
| method | `BasePlugin.hook_call_site` | `(self, in_method: Member, callee: Member, callback: Callable[[PartialChain], Any], occurrence: int=-1, priority: Optional[int]=None)` | Intercepts calls to `callee` made from inside `in_method` only. |
| method | `BasePlugin.hook_field_read` | `(self, in_method: Member, field: Any, callback: Callable[[PartialChain], Any], occurrence: int=-1, priority: Optional[int]=None)` | Intercepts reads of `field` inside `in_method`; `proceed()` returns the stored value. |
| method | `BasePlugin.hook_field_write` | `(self, in_method: Member, field: Any, callback: Callable[[PartialChain], Any], occurrence: int=-1, priority: Optional[int]=None)` | Intercepts writes of `field` inside `in_method`; `proceed(value)` stores a different value, not calling `proceed` skips the write. |
| method | `BasePlugin.hook_string_constant` | `(self, in_method: Member, text: str, callback: Callable[[PartialChain], Any], occurrence: int=-1, priority: Optional[int]=None)` | Replaces the string literal `text` inside `in_method` with what the callback returns. |
| method | `BasePlugin.hook_return_value` | `(self, in_method: Member, callback: Callable[[PartialChain], Any], occurrence: int=-1, priority: Optional[int]=None)` | Filters the values returned by the return instructions of `in_method`. |
| method | `BasePlugin.unhook_partial` | `(self, handle)` |  |
| method | `BasePlugin.logger` | `(self)` |  |
| method | `BasePlugin.logger` | `(self, value)` |  |
| method | `BasePlugin.log` | `(self, message: str)` |  |
| method | `BasePlugin.client` | `(self, account: Optional[int]=None)` |  |
| method | `BasePlugin.add_menu_item` | `(self, menu_item_data: MenuItemData)` |  |
| method | `BasePlugin.remove_menu_item` | `(self, item_id: str)` |  |

### `client_utils.py` (736 строк)

Java/Android-зависимости: `android.graphics`, `android.media`, `android.webkit`, `com.exteragram.messenger.plugins`, `java`, `java.io`, `java.lang`, `java.util`, `org.telegram.messenger`, `org.telegram.tgnet`, `org.telegram.ui`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `STAGE_QUEUE` | `= 'stageQueue'` |  |
| const | `GLOBAL_QUEUE` | `= 'globalQueue'` |  |
| const | `CACHE_CLEAR_QUEUE` | `= 'cacheClearQueue'` |  |
| const | `SEARCH_QUEUE` | `= 'searchQueue'` |  |
| const | `PHONE_BOOK_QUEUE` | `= 'phoneBookQueue'` |  |
| const | `THEME_QUEUE` | `= 'themeQueue'` |  |
| const | `EXTERNAL_NETWORK_QUEUE` | `= 'externalNetworkQueue'` |  |
| const | `PLUGINS_QUEUE` | `= 'pluginsQueue'` |  |
| func | `get_selected_account` | `()` |  |
| func | `get_hook_account` | `()` |  |
| func | `account_scope` | `(account: Optional[int])` |  |
| func | `get_queue_by_name` | `(queue_name: str)` |  |
| func | `run_on_queue` | `(fn: callable, queue_name: str=PLUGINS_QUEUE, delay: int=0)` |  |
| class | `RequestCallback` | `(dynamic_proxy(RequestDelegate))` |  |
| method | `RequestCallback.__init__` | `(self, fn: callable, account: Optional[int]=None)` |  |
| method | `RequestCallback.run` | `(self, response: TLObject, error: TLRPC.TL_error)` |  |
| func | `send_request` | `(request: Any, fn: callable, *, account: Optional[int]=None)` |  |
| func | `get_last_fragment` | `()` |  |
| func | `get_account_instance` | `(account: Optional[int]=None)` |  |
| func | `get_messages_controller` | `(account: Optional[int]=None)` |  |
| func | `get_contacts_controller` | `(account: Optional[int]=None)` |  |
| func | `get_media_data_controller` | `(account: Optional[int]=None)` |  |
| func | `get_connections_manager` | `(account: Optional[int]=None)` |  |
| func | `get_location_controller` | `(account: Optional[int]=None)` |  |
| func | `get_notifications_controller` | `(account: Optional[int]=None)` |  |
| func | `get_messages_storage` | `(account: Optional[int]=None)` |  |
| func | `get_send_messages_helper` | `(account: Optional[int]=None)` |  |
| func | `get_file_loader` | `(account: Optional[int]=None)` |  |
| func | `get_secret_chat_helper` | `(account: Optional[int]=None)` |  |
| func | `get_download_controller` | `(account: Optional[int]=None)` |  |
| func | `get_notifications_settings` | `(account: Optional[int]=None)` |  |
| func | `get_notification_center` | `(account: Optional[int]=None)` |  |
| func | `get_media_controller` | `()` |  |
| func | `get_user_config` | `(account: Optional[int]=None)` |  |
| func | `send_message` | `(params: dict, parse_mode: str=None, *, account: Optional[int]=None)` |  |
| func | `send_text` | `(peer: int, text: str, *, account: Optional[int]=None, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `send_photo` | `(peer: int, file_path: str, caption: str='', high_quality: bool=False, *, account: Optional[int]=None, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `send_document` | `(peer: int, file_path: str, caption: str='', *, account: Optional[int]=None, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `send_video` | `(peer: int, file_path: str, caption: str='', *, account: Optional[int]=None, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `send_audio` | `(peer: int, file_path: str, caption: str='', *, account: Optional[int]=None, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `edit_message` | `(message_obj: Any, text: Optional[str]=None, file_path: Optional[str]=None, with_spoiler: bool=False, *, account: Optional[int]=None, parse_mode: Optional[st...` |  |
| class | `AccountClient` | `` |  |
| method | `AccountClient.__init__` | `(self, account: int)` |  |
| method | `AccountClient.get_account_instance` | `(self)` |  |
| method | `AccountClient.get_messages_controller` | `(self)` |  |
| method | `AccountClient.get_contacts_controller` | `(self)` |  |
| method | `AccountClient.get_media_data_controller` | `(self)` |  |
| method | `AccountClient.get_connections_manager` | `(self)` |  |
| method | `AccountClient.get_location_controller` | `(self)` |  |
| method | `AccountClient.get_notifications_controller` | `(self)` |  |
| method | `AccountClient.get_messages_storage` | `(self)` |  |
| method | `AccountClient.get_send_messages_helper` | `(self)` |  |
| method | `AccountClient.get_file_loader` | `(self)` |  |
| method | `AccountClient.get_secret_chat_helper` | `(self)` |  |
| method | `AccountClient.get_download_controller` | `(self)` |  |
| method | `AccountClient.get_notifications_settings` | `(self)` |  |
| method | `AccountClient.get_notification_center` | `(self)` |  |
| method | `AccountClient.get_user_config` | `(self)` |  |
| method | `AccountClient.send_request` | `(self, request: Any, fn: callable)` |  |
| method | `AccountClient.send_message` | `(self, params: dict, parse_mode: str=None)` |  |
| method | `AccountClient.send_text` | `(self, peer: int, text: str, *, parse_mode: Optional[str]=None, **kwargs)` |  |
| method | `AccountClient.send_photo` | `(self, peer: int, file_path: str, caption: str='', high_quality: bool=False, *, parse_mode: Optional[str]=None, **kwargs)` |  |
| method | `AccountClient.send_document` | `(self, peer: int, file_path: str, caption: str='', *, parse_mode: Optional[str]=None, **kwargs)` |  |
| method | `AccountClient.send_video` | `(self, peer: int, file_path: str, caption: str='', *, parse_mode: Optional[str]=None, **kwargs)` |  |
| method | `AccountClient.send_audio` | `(self, peer: int, file_path: str, caption: str='', *, parse_mode: Optional[str]=None, **kwargs)` |  |
| method | `AccountClient.edit_message` | `(self, message_obj: Any, text: Optional[str]=None, file_path: Optional[str]=None, with_spoiler: bool=False, *, parse_mode: Optional[str]=None, **kwargs)` |  |
| func | `get_client` | `(account: Optional[int]=None)` |  |
| class | `NotificationCenterDelegate` | `(dynamic_proxy(NotificationCenter.NotificationCenterDelegate))` |  |
| method | `NotificationCenterDelegate.__init__` | `(self)` |  |
| method | `NotificationCenterDelegate.didReceivedNotification` | `(self, id: int, account: int, args: jarray(Object))` |  |

### `dev_server.py` (608 строк)

Java/Android-зависимости: `com.exteragram.messenger.plugins`, `java`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `DebuggerPlatform` | `(enum.Enum)` |  |
| const | `DebuggerPlatform.PyCharm` | `= 'pycharm'` |  |
| const | `DebuggerPlatform.VSCode` | `= 'vscode'` |  |
| class | `Callback` | `(dynamic_proxy(Utilities.Callback))` |  |
| method | `Callback.__init__` | `(self, fn: Callable[[Any], None])` |  |
| method | `Callback.run` | `(self, arg)` |  |
| class | `DebuggerEventListener` | `(BasePlugin)` |  |
| method | `DebuggerEventListener.__init__` | `(self, host: str, port: int, platform: DebuggerPlatform)` |  |
| method | `DebuggerEventListener.on_app_event` | `(self, event_type: str)` |  |
| class | `DevServer` | `` |  |
| const | `DevServer.SOCKET_NAME` | `= 'exteragram_devserver'` |  |
| const | `DevServer.ADB_UIDS` | `= (0, 2000)` |  |
| const | `DevServer.SOCKET_TIMEOUT` | `= 600` |  |
| const | `DevServer.BUFFER_SIZE` | `= 4096` |  |
| const | `DevServer.PYCHARM_DEBUGGER_DIR` | `= os.path.join(FileLoader.getDirectory(FileLoader.MEDIA_DIR_FI` |  |
| method | `DevServer.start_server` | `(cls)` |  |
| method | `DevServer.stop_server` | `(cls)` |  |
| method | `DevServer.setup_remote_debugging` | `(cls, host: str, port: int, platform: DebuggerPlatform)` |  |
| method | `DevServer.stop_remote_debugging` | `(cls, platform: DebuggerPlatform)` |  |

### `file_utils.py` (1127 строк)

Java/Android-зависимости: `android.app`, `android.graphics.drawable`, `com.android.dx`, `com.chaquo.python`, `com.exteragram.messenger.plugins`, `de.robv.android.xposed.XC_MethodHook$MethodHookParam`, `java`, `java.io`, `java.lang`, `java.lang.Boolean`, `java.lang.Class`, `java.lang.Integer`, `java.lang.StackTraceElement`, `java.lang.Thread`, `java.lang.reflect`, `java.lang.reflect.Field`, `java.util.concurrent`, `org.telegram.messenger`, `org.telegram.messenger.UserConfig`, `org.telegram.tgnet.TLRPC$Document`, `org.telegram.tgnet.TLRPC$Message`, `org.telegram.ui.ActionBar`, `org.telegram.ui.Cells`, `org.telegram.ui.Components`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `get_plugins_dir` | `()` |  |
| func | `get_cache_dir` | `()` |  |
| func | `get_files_dir` | `()` |  |
| func | `get_images_dir` | `()` |  |
| func | `get_videos_dir` | `()` |  |
| func | `get_audios_dir` | `()` |  |
| func | `get_documents_dir` | `()` |  |
| func | `read_file` | `(file_path: str)` |  |
| func | `read_file_bytes` | `(file_path: str)` |  |
| func | `write_file` | `(file_path: str, content: str)` |  |
| func | `write_file_bytes` | `(file_path: str, content: bytes)` |  |
| func | `delete_file` | `(file_path: str)` |  |
| func | `ensure_dir_exists` | `(dir_path: str)` |  |
| func | `list_dir` | `(path: str, recursive: bool=False, include_files: bool=True, include_dirs: bool=False, extensions: Optional[List[str]]=None)` |  |
| class | `staticproperty` | `` |  |
| method | `staticproperty.__init__` | `(self, fget)` |  |
| class | `FilesController` | `` |  |
| method | `FilesController.DIRECT_FILE_ICONS` | `()` |  |
| method | `FilesController.SUPPORT_ICONS` | `()` |  |
| method | `FilesController.register` | `(cls, file_info: FileInfo)` |  |
| method | `FilesController.unregister` | `(cls, ext: str, secret: str)` |  |

### `hook_utils.py` (236 строк)

Java/Android-зависимости: `java`, `java.lang.Class`, `java.lang.Object`, `java.lang.reflect.Array`, `org.telegram.messenger.ApplicationLoader`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `find_class` | `(class_name: str)` |  |
| func | `get_private_field` | `(obj: JavaObject, field_name: str)` |  |
| func | `set_private_field` | `(obj: JavaObject, field_name: str, new_value: Any)` |  |
| func | `java_class` | `(clazz: Any)` | Returns the `java.lang.Class` for a class name, a `find_class(...)` result or a `Class`. |
| func | `get_method` | `(clazz: Any, method_name: str, *param_types: Any)` | Finds a method declared in `clazz` or its superclasses and makes it accessible. |
| func | `get_constructor` | `(clazz: Any, *param_types: Any)` | Finds a constructor of `clazz` and makes it accessible. |
| func | `get_field` | `(clazz: Any, field_name: str)` | Finds a field declared in `clazz` or its superclasses and makes it accessible. |
| func | `get_static_private_field` | `(clazz: JavaClass, field_name: str)` |  |
| func | `set_static_private_field` | `(clazz: JavaClass, field_name: str, new_value: Any)` |  |

### `intents.py` (1053 строк)

Java/Android-зависимости: `android.content`, `android.net`, `com.android.dx`, `com.chaquo.python`, `com.exteragram.messenger.utils`, `de.robv.android.xposed.XC_MethodHook$MethodHookParam`, `java`, `java.lang`, `java.lang.reflect`, `java.util`, `java.util.Iterator`, `java.util.Map$Entry`, `java.util.Set`, `java.util.concurrent`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `IntentsManager` | `` |  |
| method | `IntentsManager.parse` | `(url: str)` |  |
| method | `IntentsManager.new_global_before_handler` | `(cls, info: HandlerInfo)` |  |
| method | `IntentsManager.new_global_after_handler` | `(cls, info: HandlerInfo)` |  |
| method | `IntentsManager.unhandle` | `(cls, handler_id: str)` |  |

### `log_utils.py` (686 строк)

Java/Android-зависимости: `android.util`, `com.exteragram.messenger`, `java.lang`, `java.lang.reflect`, `java.util`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `LogLevel` | `(IntEnum)` |  |
| const | `LogLevel.VERBOSE` | `= 2` |  |
| const | `LogLevel.DEBUG` | `= 3` |  |
| const | `LogLevel.INFO` | `= 4` |  |
| const | `LogLevel.WARNING` | `= 5` |  |
| const | `LogLevel.ERROR` | `= 6` |  |
| const | `LogLevel.OFF` | `= 100` |  |
| class | `LogRecord` | `` |  |
| method | `LogRecord.__init__` | `(self, level: LogLevel, tag: str, message: str, location: Optional[str], tb: Optional[str], created: float)` |  |
| method | `LogRecord.text` | `(self)` |  |
| class | `Logger` | `` |  |
| method | `Logger.__init__` | `(self, tag: str, *, show_location: bool=True)` |  |
| method | `Logger.tag` | `(self)` |  |
| method | `Logger.level` | `(self)` |  |
| method | `Logger.level` | `(self, value: Union[LogLevel, int, str, None])` |  |
| method | `Logger.effective_level` | `(self)` |  |
| method | `Logger.is_enabled_for` | `(self, level: Union[LogLevel, int, str])` |  |
| method | `Logger.child` | `(self, name: str)` |  |
| method | `Logger.verbose` | `(self, msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.debug` | `(self, msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.info` | `(self, msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.warning` | `(self, msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.error` | `(self, msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.exception` | `(self, msg: Any, *args, stacklevel: int=1)` |  |
| method | `Logger.log` | `(self, level: Union[LogLevel, int, str], msg: Any, *args, exc_info: Any=None, stacklevel: int=1)` |  |
| method | `Logger.dump` | `(self, obj: Any, label: Optional[str]=None, *, level: Union[LogLevel, int, str]=LogLevel.DEBUG, depth: int=2, max_items: int=20, stacklevel: int=1)` |  |
| method | `Logger.timed` | `(self, label: str, level: Union[LogLevel, int, str]=LogLevel.DEBUG)` |  |
| method | `Logger.add_handler` | `(self, handler: Callable[[LogRecord], Any])` |  |
| method | `Logger.remove_handler` | `(self, handler: Callable[[LogRecord], Any])` |  |
| func | `get_logger` | `(name: Optional[str]=None)` |  |
| func | `dump` | `(obj: Any, depth: int=2, max_items: int=20)` |  |

### `markdown_utils.py` (318 строк)

Java/Android-зависимости: `org.telegram.tgnet`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `TLEntityType` | `(Enum)` |  |
| const | `TLEntityType.CODE` | `= 'code'` |  |
| const | `TLEntityType.PRE` | `= 'pre'` |  |
| const | `TLEntityType.STRIKETHROUGH` | `= 'strikethrough'` |  |
| const | `TLEntityType.TEXT_LINK` | `= 'text_link'` |  |
| const | `TLEntityType.BOLD` | `= 'bold'` |  |
| const | `TLEntityType.ITALIC` | `= 'italic'` |  |
| const | `TLEntityType.UNDERLINE` | `= 'underline'` |  |
| const | `TLEntityType.SPOILER` | `= 'spoiler'` |  |
| const | `TLEntityType.CUSTOM_EMOJI` | `= 'custom_emoji'` |  |
| class | `RawEntity` | `` | An object representing the TLRPC message entity. Contains offset, length, and other optional parameters. Must be converted to a TLRPC object using ``RawEntity.to_tlrpc_object()`` before sending. |
| field | `RawEntity.type` | `: TLEntityType` |  |
| field | `RawEntity.offset` | `: int` |  |
| field | `RawEntity.length` | `: int` |  |
| field | `RawEntity.language` | `: Optional[str] = None` |  |
| field | `RawEntity.url` | `: Optional[str] = None` |  |
| field | `RawEntity.document_id` | `: Optional[int] = None` |  |
| method | `RawEntity.to_tlrpc_object` | `(self)` |  |
| class | `ParsedMessage` | `` | An object containing the final message text and a list of RawEntity objects. |
| field | `ParsedMessage.text` | `: str` |  |
| field | `ParsedMessage.entities` | `: Tuple[RawEntity, ...]` |  |
| func | `count_chars_until` | `(string: str, stop_chars: str, start_index: int=0)` | Returns the number of characters in 'string' (starting at 'start_index') until any character from 'stop_chars' is encountered. |
| func | `to_utf16_len` | `(s: str)` |  |
| func | `parse_markdown` | `(markdown: str)` | :raises SyntaxError: when encountered incorrect markdown syntax |
| const | `TLRPC_ENTITIES_MAP` | `= {TLEntityType.CODE: TLRPC.TL_messageEntityCode, TLEntityType` |  |

### `plugin_settings.py` (164 строк)

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `init` | `(plugins_dir_path: str, all_shared_prefs)` |  |
| func | `get_setting` | `(plugin_id: str, key: str, default: Any)` |  |
| func | `set_setting` | `(plugin_id: str, key: str, value: Any)` |  |
| func | `clear_settings` | `(plugin_id: str)` |  |
| func | `get_all_settings` | `(plugin_id: str)` |  |
| func | `set_all_settings` | `(plugin_id: str, settings: dict)` |  |

### `elyxcore/__init__.py` (106 строк)

> Public API for structured Elyx plugins.

Java/Android-зависимости: `android.view`, `java.lang`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `get_environment` | `()` | Return assets, settings, strings and metadata for the calling plugin. |
| func | `import_module` | `(name: str, package: str \| None=None)` | Import a module relative to the calling plugin when it exists locally. |

### `elyxcore/_dev_server.py` (275 строк) — внутренний модуль

Java/Android-зависимости: `java.io`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `ElyxDevServer` | `` |  |
| const | `ElyxDevServer.original_method` | `= None` |  |
| const | `ElyxDevServer.hash_cache` | `= {}` |  |
| method | `ElyxDevServer.get_file_hash` | `(cls, filepath)` |  |
| method | `ElyxDevServer.setup` | `(cls)` |  |
| method | `ElyxDevServer.teardown` | `(cls)` |  |
| method | `ElyxDevServer.cmpss` | `(rs)` |  |

### `elyxcore/_engine.py` (86 строк) — внутренний модуль

Java/Android-зависимости: `com.exteragram.messenger.plugins`

### `elyxcore/_importer.py` (413 строк) — внутренний модуль

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `PLUGIN_NAMESPACE` | `= 'ElyxPlugins'` |  |
| const | `PUBLIC_MODULE` | `= 'elyx'` |  |
| class | `ElyxImporter` | `(importlib.abc.MetaPathFinder, importlib.abc.Loader)` |  |
| method | `ElyxImporter.__init__` | `(self)` |  |
| method | `ElyxImporter.invalidate_caches` | `(self)` |  |
| method | `ElyxImporter.get_caller_root` | `(self)` |  |
| method | `ElyxImporter.get_caller_plugin` | `(self)` |  |
| method | `ElyxImporter.import_module` | `(self, name: str, package: Optional[str]=None)` | Import a local module without creating an unqualified sys.modules alias. |
| method | `ElyxImporter.find_spec` | `(self, fullname: str, path=None, target=None)` |  |
| method | `ElyxImporter.create_module` | `(self, spec)` |  |
| method | `ElyxImporter.exec_module` | `(self, module)` |  |
| method | `ElyxImporter.unload_plugin` | `(self, plugin_id: str)` |  |
| method | `ElyxImporter.unload_all` | `(self)` |  |
| func | `setup` | `()` |  |
| func | `stop` | `()` |  |

### `elyxcore/_install.py` (345 строк) — внутренний модуль

Java/Android-зависимости: `android.content`, `android.graphics`, `android.graphics.drawable`, `android.text`, `android.util`, `android.view`, `android.view.inputmethod`, `android.widget`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.ui.components`, `java`, `java.io`, `java.lang`, `java.util`, `org.telegram.messenger`, `org.telegram.ui.ActionBar`, `org.telegram.ui.Components`, `org.telegram.ui.Stories.recorder`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `InstallAlert` | `` |  |
| method | `InstallAlert.show_password_dialog` | `(cls, lib, fragment, params)` |  |
| method | `InstallAlert.show` | `(cls, lib, fragment, plugin: ElyxPlugin, params)` |  |

### `elyxcore/_plugin.py` (769 строк) — внутренний модуль

Java/Android-зависимости: `android.view`, `androidx.core.content`, `com.chaquo.python`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.hooks`, `com.exteragram.messenger.plugins.models`, `com.exteragram.messenger.plugins.pip`, `com.exteragram.messenger.plugins.ui`, `com.exteragram.messenger.plugins.ui.components`, `java`, `java.lang`, `java.util`, `org.mvel2`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `ELYX_ID` | `= 'elyxcore'` |  |
| func | `dlog` | `(msg: str)` |  |
| const | `ALLOWED_METAINFO` | `= ['name', 'description', 'version', 'icon', 'id', 'author', '` |  |
| const | `BASE_METAINFO` | `= {'description': 'Description not provided', 'version': '1.0.` |  |
| const | `ENGINE_ID` | `= 'elyx-py'` |  |
| const | `REFMAP_FILES` | `= ('refmap.yaml', 'refmap.yml', 'refmap.json')` |  |
| const | `METAINFO_FILES` | `= ('metainfo.yaml', 'metainfo.yml', 'metainfo.json')` |  |
| class | `ArchiveEncryptionError` | `(Exception)` | Exception for archive encryption. |
| class | `SecurityError` | `(Exception)` | Exception for an unsafe path in a bundled wheel. |
| class | `ValidationError` | `(Exception)` | Exception for invalid plugin structure. |
| class | `InvalidPluginError` | `(Exception)` | Exception for invalid plugin. |
| method | `InvalidPluginError.plugin_class_not_found` | `(cls, main_file_path)` |  |
| class | `RequiredPlugin` | `(Exception)` | Exception for required plugin. |
| method | `RequiredPlugin.__init__` | `(self, plugin_id, required_version: Optional[str]=None, link_to_download: Optional[str]=None, current_version=None)` |  |
| class | `ElyxPlugin` | `` |  |
| field | `ElyxPlugin.instances` | `: Dict[str, 'ElyxPlugin'] = {}` |  |
| field | `ElyxPlugin.instances_by_id` | `: Dict[str, 'ElyxPlugin'] = {}` |  |
| method | `ElyxPlugin.from_archive` | `(cls, plzip: ZipFile)` |  |
| method | `ElyxPlugin.read_metainfo` | `(cls, plzip: ZipFile)` |  |
| method | `ElyxPlugin.is_plugin_dir` | `(dir_path)` |  |
| method | `ElyxPlugin.__init__` | `(self, dir_path: Optional[str]=None, plzip: Optional[ZipFile]=None, pwd: Optional[str]=None, raise_errors: bool=True)` |  |
| method | `ElyxPlugin.validation_result` | `(self)` |  |
| method | `ElyxPlugin.structure` | `(self)` |  |
| method | `ElyxPlugin.init` | `(self)` |  |
| method | `ElyxPlugin.get_environment_vars` | `(self)` |  |
| method | `ElyxPlugin.get_strings` | `(self, files=None)` |  |
| method | `ElyxPlugin.load_structure` | `(self)` |  |
| method | `ElyxPlugin.validate` | `(self, files: Dict[str, Union[ZipInfo, Path]])` |  |
| method | `ElyxPlugin.get_file_content` | `(self, f: Optional[Union[ZipInfo, Path]]=None, path: Optional[str]=None)` |  |
| method | `ElyxPlugin.get_refmap` | `(self, files: Dict[str, Union[ZipInfo, Path]])` |  |
| method | `ElyxPlugin.get_metainfo` | `(self, files: Optional[Dict[str, Union[ZipInfo, Path]]]=None, with_defaults: bool=True)` |  |
| method | `ElyxPlugin.get_validation_result` | `(self)` |  |
| method | `ElyxPlugin.is_custom_icon` | `(self)` |  |
| method | `ElyxPlugin.get_icon_path` | `(self)` |  |
| const | `WHEEL_ROOTS_FILE` | `= 'roots.json'` |  |

### `elyxcore/_plugin_engine.py` (1141 строк) — внутренний модуль

Java/Android-зависимости: `android.view`, `androidx.core.content`, `com.chaquo.python`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.hooks`, `com.exteragram.messenger.plugins.models`, `com.exteragram.messenger.plugins.pip`, `com.exteragram.messenger.plugins.ui`, `com.exteragram.messenger.plugins.ui.components`, `com.exteragram.messenger.plugins.xposed`, `java`, `java.io`, `java.lang`, `java.util`, `org.mvel2`, `org.telegram.messenger`, `org.telegram.tgnet`, `org.telegram.ui`, `org.telegram.ui.ActionBar`, `org.telegram.ui.Components`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `ELYX_ID` | `= 'elyxcore'` |  |
| func | `dlog` | `(msg: str)` |  |
| class | `ElyxEngine` | `(Base)` |  |
| const | `ElyxEngine.ID` | `= 'elyx-py'` |  |
| const | `ElyxEngine.DEFAULT_EXTENSIONS` | `= ['elyx', 'eaf']` |  |
| field | `ElyxEngine.instance` | `: Optional['ElyxEngine'] = None` |  |
| method | `ElyxEngine.__init__` | `(self)` |  |
| method | `ElyxEngine.plugins_dir` | `(self)` |  |
| method | `ElyxEngine.plugins_dir_path` | `(self)` |  |
| method | `ElyxEngine.plugin_dir` | `(self, plugin_id)` |  |
| method | `ElyxEngine.isPlugin` | `(self, file: File \| None, message_object: MessageObject \| None=None)` |  |
| method | `ElyxEngine.parsePluginMetadata` | `(self, filePath: str)` |  |
| method | `ElyxEngine.isEngineAvailable` | `(self)` |  |
| method | `ElyxEngine.get_setting` | `(key, default=None)` |  |
| method | `ElyxEngine.log` | `(message)` |  |
| method | `ElyxEngine.load_from_archive` | `(self, pl: ElyxPlugin, enable_after_install: bool=False, on_complete: Optional[Callable[[], None]]=None, on_error: Optional[Callable[[Any], None]]=None, dele...` |  |
| method | `ElyxEngine.clear_py_cache` | `(self, plugin_id: Optional[str]=None)` |  |
| method | `ElyxEngine.remove_pycache` | `(cls, dir_path: str)` |  |
| method | `ElyxEngine.init` | `(self, callback, force=False)` |  |
| method | `ElyxEngine.run_callback` | `(callback, *args, on_ui_thread=False, on_queue=False, **kwargs)` |  |
| method | `ElyxEngine.checkDevServer` | `(self)` |  |
| method | `ElyxEngine.shutdown` | `(self, callback)` |  |
| method | `ElyxEngine.notify_plugins_changed` | `()` |  |
| method | `ElyxEngine.unloadPlugins` | `(self, callback: Any=None)` |  |
| method | `ElyxEngine.loadPlugins` | `(self, callback)` |  |
| method | `ElyxEngine.loadPlugin` | `(self, pluginId: str, filePath: str, enable_after_install=None, callback=None, delegate=None, callback_on_ui_thread=True)` |  |
| method | `ElyxEngine.unloadPlugin` | `(self, pluginId: str)` |  |
| method | `ElyxEngine.cleanup_plugin` | `(plugin_id: str, pc: Optional[PluginsController]=None)` |  |
| method | `ElyxEngine.setPluginEnabled` | `(self, pluginId: str, enabled: bool, callback, callback_on_ui_thread=True)` |  |
| method | `ElyxEngine.deletePlugin` | `(self, pluginId: str, callback)` |  |
| method | `ElyxEngine.getPluginPath` | `(self, plugin_id: str)` |  |
| method | `ElyxEngine.canOpenInExternalApp` | `(self)` |  |
| method | `ElyxEngine.openInExternalApp` | `(self, plugin_id: str)` |  |
| method | `ElyxEngine.sharePlugin` | `(self, plugin_id: str)` |  |
| method | `ElyxEngine.loadPluginSettings` | `(self, plugin_id: str)` |  |
| method | `ElyxEngine.revert_to_java_settings` | `(settings: list)` |  |
| method | `ElyxEngine.getPluginSetting` | `(self, pluginId, key, defaultValue)` |  |
| method | `ElyxEngine.setPluginSetting` | `(self, pluginId, key, value)` |  |
| method | `ElyxEngine.clearPluginSettings` | `(self, plugin_id)` |  |
| method | `ElyxEngine.getAllPluginSettings` | `(self, pluginId, to_java_map=True)` |  |
| method | `ElyxEngine.executeOnAppEvent` | `(self, eventType)` |  |
| method | `ElyxEngine.executeHook` | `(self, instance, initial_value, result_key, caller)` |  |
| method | `ElyxEngine.executePreRequestHook` | `(self, requestName, account, request, pluginId)` |  |
| method | `ElyxEngine.executePostRequestHook` | `(self, requestName, account, response, error, pluginId)` |  |
| method | `ElyxEngine.executeUpdateHook` | `(self, updateName, account, update, pluginId)` |  |
| method | `ElyxEngine.executeUpdatesHook` | `(self, containerName, account, updates, pluginId)` |  |
| method | `ElyxEngine.executeSendMessageHook` | `(self, account, params, pluginId)` |  |
| method | `ElyxEngine.showInstallDialog` | `(self, fragment, params)` |  |
| method | `ElyxEngine.loadPluginFromFile` | `(self, filePath, pluginMetadata, callback, delegate)` |  |
| method | `ElyxEngine.open_plugin_settings_by_id` | `(self, plugin_id, fragment)` |  |
| method | `ElyxEngine.open_plugin_settings_by_plugin` | `(self, plugin, fragment)` |  |
| method | `ElyxEngine.open_plugin_setting_by_plugin` | `(self, plugin, link_alias, fragment)` |  |
| method | `ElyxEngine.open_plugin_setting_by_id` | `(self, plugin_id, link_alias, fragment)` |  |

### `elyxcore/assets.py` (274 строк)

Java/Android-зависимости: `android.graphics`, `android.graphics.drawable`, `java.io`, `org.telegram.messenger`, `org.telegram.ui.Components`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `load_data_file` | `(path: Union[Path, ZipInfo], plzip: Optional[ZipFile]=None)` |  |
| func | `normalize_name` | `(name: str)` |  |
| class | `AssetNotFoundException` | `(Exception)` |  |
| method | `AssetNotFoundException.__init__` | `(self, name: str, dir_path: Optional[str]=None)` |  |
| class | `AssetsDirNotFoundException` | `(Exception)` |  |
| method | `AssetsDirNotFoundException.__init__` | `(self, dir_path: Optional[str]=None)` |  |
| class | `Asset` | `` |  |
| method | `Asset.__init__` | `(self, dir_path: Union[str, Path, File], filename: str, name: str)` | Args:     dir_path (Union[str, Path, File]) - path of asset root directory     filename (str) - name of asset file     name (str) - name of asset |
| method | `Asset.from_path` | `(cls, path: Union[str, Path, File])` |  |
| method | `Asset.temp_asset_from_url` | `(cls, url: str, filename: str)` |  |
| method | `Asset.path_str` | `(self)` |  |
| method | `Asset.path` | `(self)` |  |
| method | `Asset.java_file` | `(self)` |  |
| method | `Asset.to_image_location` | `(self)` |  |
| method | `Asset.to_drawable` | `(self)` |  |
| method | `Asset.to_bitmap_drawable` | `(self, width: int=32, height: int=32)` |  |
| method | `Asset.to_lottie_drawable` | `(self, width: int=32, height: int=32)` |  |
| method | `Asset.to_svg_drawable` | `(self, width: Optional[int]=None, height: Optional[int]=None, *args)` |  |
| method | `Asset.to_svg_thumb` | `(self, color_key: int, alpha: float)` |  |
| method | `Asset.to_svg_bitmap` | `(self, width: int=32, height: int=32, white: bool=False)` |  |
| method | `Asset.content_bytes` | `(self)` |  |
| method | `Asset.content_string` | `(self)` |  |
| method | `Asset.content_json` | `(self)` |  |
| method | `Asset.content_yaml` | `(self)` |  |
| method | `Asset.content` | `(self)` |  |
| class | `Assets` | `` |  |
| method | `Assets.__init__` | `(self, dir_path: Union[str, Path])` |  |
| method | `Assets.parent` | `(self)` |  |
| method | `Assets.get` | `(self, name: str)` |  |

### `elyxcore/localization.py` (187 строк)

Java/Android-зависимости: `android.view`, `androidx.core.content`, `com.chaquo.python`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.hooks`, `com.exteragram.messenger.plugins.models`, `com.exteragram.messenger.plugins.pip`, `com.exteragram.messenger.plugins.ui`, `com.exteragram.messenger.plugins.ui.components`, `java`, `java.lang`, `java.util`, `org.mvel2`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `ELYX_ID` | `= 'elyxcore'` |  |
| func | `dlog` | `(msg: str)` |  |
| class | `Strings` | `(LazyDict)` |  |
| method | `Strings.__init__` | `(self, all_strings: Dict[str, Dict])` |  |
| method | `Strings.get_current_language` | `()` |  |
| method | `Strings.get` | `(self, key: str)` |  |
| method | `Strings.get` | `(self, key: str, default)` |  |
| method | `Strings.get` | `(self, key: str, default=None)` |  |
| method | `Strings.get_with_locale` | `(self, key: str, default=None, locale: str=None)` |  |
| method | `Strings.pluralization_string` | `(number: int, words: List[str])` |  |
| method | `Strings.pluralize` | `(self, number: int, key: str)` |  |

### `elyxcore/settings.py` (51 строк)

Java/Android-зависимости: `com.exteragram.messenger.plugins`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `SettingsController` | `` |  |
| method | `SettingsController.__init__` | `(self, plugin_id: str)` |  |
| method | `SettingsController.get_settings` | `(self)` |  |
| method | `SettingsController.get_setting` | `(self, key: str, default=None)` |  |
| method | `SettingsController.get` | `(self, key: str, default=None)` |  |
| method | `SettingsController.set_setting` | `(self, key: str, value, reload_settings=False)` |  |
| method | `SettingsController.set` | `(self, key: str, value, reload_settings=False)` |  |
| method | `SettingsController.clear_settings` | `(self)` |  |

### `elyxcore/utils.py` (175 строк)

Java/Android-зависимости: `java`, `java.lang`, `java.util`, `org.mvel2`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `gen` | `(java_class: Union[Class, type[Class]], method_name: str, return_value: bool=False, default_value=None)` | Generate class implements an interface |
| func | `gen2` | `(java_class, return_value: bool=False, **methods)` |  |
| func | `mvel_execute` | `(script: str, data: Optional[dict \| HashMap], to_type=None, java_instance=None)` | Execute MVEL script |
| class | `LazyDict` | `(dict)` |  |
| func | `safe_run_on_queue` | `(fn)` |  |
| func | `safe_func` | `(fn)` |  |
| func | `hash_map` | `(dict_)` |  |
| func | `resize_image` | `(image: bytes, width: int, height: int)` |  |

### `extera_utils/__init__.py` (1 строк)

### `extera_utils/classes.py` (1628 строк)

Java/Android-зависимости: `com.chaquo.python.PyObject`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.utils`, `java`, `java.lang`, `java.lang.Object`, `java.lang.ref`, `java.lang.reflect`, `java.lang.reflect.Field`, `java.util`, `org.telegram.messenger`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `collect_peers` | `()` |  |
| func | `release_plugin` | `(plugin_id=None)` |  |
| class | `JField` | `` |  |
| method | `JField.__init__` | `(self, field_type, *, default=_UNSET, modifiers='public', methods=None)` |  |
| class | `JMvelMethod` | `` |  |
| method | `JMvelMethod.__init__` | `(self, metadata)` |  |
| class | `ClassInterceptor` | `(dynamic_proxy(Utilities.Callback3Return))` |  |
| method | `ClassInterceptor.__init__` | `(self, fn=None, pyclass=None, **kwargs)` |  |
| method | `ClassInterceptor.run` | `(self, instance, method_name, args)` |  |
| func | `class_proxy` | `(clazz, *, fn: Optional[callable]=None, interceptor=None, methods=None, constructors=None, custom_name=None, **kwargs)` |  |
| class | `JHelper` | `` |  |
| method | `JHelper.Override` | `(*signature, arg_types=None, modifiers='public', throws=None, name=None)` |  |
| method | `JHelper.Overload` | `(name, arg_types, *, modifiers='public', throws=None)` |  |
| method | `JHelper.Method` | `(*signature, return_type=None, arg_types=None, modifiers='public', throws=None, name=None)` |  |
| method | `JHelper.MVELMethod` | `(*, code, return_type=None, arguments=None, arg_types=None, modifiers='public', throws=None, name=None, override=False)` |  |
| method | `JHelper.MVELOverride` | `(*signature, code, arguments=None, arg_types=None, modifiers='public', throws=None, name=None)` |  |
| method | `JHelper.Constructor` | `(*signature, arg_types=None)` |  |
| method | `JHelper.PreConstructor` | `(*signature, arg_types=None)` |  |
| method | `JHelper.Field` | `(field_type, *, default=_UNSET, modifiers='public', methods=None)` |  |
| method | `JHelper.GetMethod` | `(name=None, *, modifiers='public')` |  |
| method | `JHelper.SetMethod` | `(name=None, *, modifiers='public')` |  |
| method | `JHelper.ClassBuilder` | `()` |  |
| class | `Base` | `` |  |
| method | `Base.__init__` | `(self, *args, **kwargs)` |  |
| method | `Base.on_pre_init` | `(cls, *args)` |  |
| method | `Base.on_post_init` | `(self, *args)` |  |
| method | `Base.java` | `(self)` |  |
| method | `Base.this` | `(self)` |  |
| method | `Base.jrelease` | `(self)` |  |
| method | `Base.on_release` | `(self)` |  |
| method | `Base.extends` | `(cls, java_class, *interfaces, methods=None, constructors=None, custom_name=None)` |  |
| method | `Base.bind` | `(cls, java_class, *interfaces, methods=None, constructors=None, custom_name=None)` |  |
| method | `Base.java_class` | `(cls)` |  |
| method | `Base.from_java` | `(cls, instance, *, init_args=None)` |  |
| method | `Base.new_java_instance` | `(cls, *args)` |  |
| method | `Base.new_instance` | `(cls, *args, init_args=None)` |  |
| class | `PyObj` | `(Base)` |  |
| const | `PyObj.obj` | `= jfield('com.chaquo.python.PyObject')` |  |
| method | `PyObj.create` | `(cls, obj)` |  |

### `extera_utils/get_caller.py` (102 строк)

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `ELYX_PLUGIN_NAMESPACE` | `= 'ElyxPlugins'` |  |
| func | `get_plugin_id` | `(fn=None)` |  |

### `extera_utils/lifecycle.py` (298 строк)

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `PluginScope` | `` |  |
| method | `PluginScope.__init__` | `(self, plugin_id)` |  |
| method | `PluginScope.close` | `(self)` |  |
| method | `PluginScope.register_cleanup` | `(self, cleanup)` |  |
| class | `ManagedCallback` | `` |  |
| method | `ManagedCallback.__init__` | `(self, fn, scope=None, once=False, allow_stopped=False, cleanup_task=False)` |  |
| method | `ManagedCallback.cancelled` | `(self)` |  |
| method | `ManagedCallback.set_cancel` | `(self, cancel)` |  |
| method | `ManagedCallback.cancel` | `(self)` |  |
| func | `begin` | `(plugin_id)` |  |
| func | `stop` | `(plugin_id)` |  |
| func | `stop_all` | `()` |  |
| func | `capture_scope` | `(fn=None)` |  |
| func | `bind` | `(fn, *, once=False)` |  |
| func | `plugin_context` | `(plugin_id)` |  |
| func | `cleanup_context` | `(scope)` |  |
| func | `bind_task` | `(fn, *, once=False, scope=None)` |  |
| func | `bind_request` | `(fn)` |  |

### `extera_utils/metadata_parser.py` (98 строк)

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| const | `MAX_SOURCE_BYTES` | `= 64 * 1024 * 1024` |  |
| const | `MAX_STATEMENT_CHARS` | `= 64 * 1024` |  |
| const | `ALLOWED_KEYS` | `= {'__id__', '__name__', '__description__', '__author__', '__v` |  |
| func | `get_metadata` | `(file_path)` |  |

### `extera_utils/text_formatting.py` (626 строк)

Java/Android-зависимости: `org.telegram.tgnet`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| func | `add_surrogates` | `(text: str)` |  |
| func | `remove_surrogates` | `(text: str)` |  |
| class | `TLEntityType` | `(Enum)` |  |
| const | `TLEntityType.CODE` | `= 'code'` |  |
| const | `TLEntityType.PRE` | `= 'pre'` |  |
| const | `TLEntityType.STRIKETHROUGH` | `= 'strikethrough'` |  |
| const | `TLEntityType.TEXT_LINK` | `= 'text_link'` |  |
| const | `TLEntityType.BOLD` | `= 'bold'` |  |
| const | `TLEntityType.ITALIC` | `= 'italic'` |  |
| const | `TLEntityType.UNDERLINE` | `= 'underline'` |  |
| const | `TLEntityType.SPOILER` | `= 'spoiler'` |  |
| const | `TLEntityType.CUSTOM_EMOJI` | `= 'custom_emoji'` |  |
| const | `TLEntityType.BLOCKQUOTE` | `= 'blockquote'` |  |
| method | `TLEntityType.from_` | `(cls, entity)` |  |
| class | `RawEntity` | `` |  |
| method | `RawEntity.TLRPC_ENTITIES_MAP` | `(self)` |  |
| field | `RawEntity.type` | `: TLEntityType` |  |
| field | `RawEntity.offset` | `: int` |  |
| field | `RawEntity.length` | `: int` |  |
| field | `RawEntity.language` | `: Optional[str] = None` |  |
| field | `RawEntity.url` | `: Optional[str] = None` |  |
| field | `RawEntity.document_id` | `: Optional[int] = None` |  |
| field | `RawEntity.collapsed` | `: Optional[bool] = None` |  |
| method | `RawEntity.to_tlrpc_object` | `(self)` |  |
| class | `Parser` | `(HTMLParser)` |  |
| method | `Parser.__init__` | `(self)` |  |
| method | `Parser.handle_starttag` | `(self, tag, attrs)` |  |
| method | `Parser.handle_data` | `(self, data)` |  |
| method | `Parser.handle_endtag` | `(self, tag)` |  |
| class | `HTML` | `` |  |
| method | `HTML.parse` | `(text: str)` |  |
| method | `HTML.unparse` | `(text: str, entities: list)` |  |
| const | `BOLD_DELIM` | `= '*'` |  |
| const | `ITALIC_DELIM` | `= '_'` |  |
| const | `UNDERLINE_DELIM` | `= '__'` |  |
| const | `STRIKE_DELIM` | `= '~'` |  |
| const | `SPOILER_DELIM` | `= '\|\|'` |  |
| const | `CODE_DELIM` | `= '`'` |  |
| const | `PRE_DELIM` | `= '```'` |  |
| const | `BLOCKQUOTE_DELIM` | `= '>'` |  |
| const | `BLOCKQUOTE_EXPANDABLE_DELIM` | `= '**>'` |  |
| const | `BLOCKQUOTE_EXPANDABLE_END_DELIM` | `= '\|\|'` |  |
| const | `MARKDOWN_RE` | `= re.compile('({d})\|(!?)\\[(.+?)]\\((.+?)\\)'.format(d='\|'.joi` |  |
| const | `OPENING_TAG` | `= '<{}>'` |  |
| const | `CLOSING_TAG` | `= '</{}>'` |  |
| const | `URL_MARKUP` | `= '<a href="{}">{}</a>'` |  |
| const | `EMOJI_MARKUP` | `= '<emoji id={}>{}</emoji>'` |  |
| const | `FIXED_WIDTH_DELIMS` | `= [CODE_DELIM, PRE_DELIM]` |  |
| const | `MARKDOWN_ESCAPABLE_CHARS` | `= '\\_*[]()~`\|>!'` |  |
| const | `ESCAPED_MARKDOWN_RE` | `= re.compile('\\\\([{}])'.format(re.escape(MARKDOWN_ESCAPABLE_` |  |
| func | `replace_once` | `(source: str, old: str, new: str, start: int)` |  |
| class | `Markdown` | `` |  |
| method | `Markdown.protect_escaped_chars` | `(text: str)` |  |
| method | `Markdown.restore_escaped_chars` | `(text: str, escaped_chars: Dict[str, str])` |  |
| method | `Markdown.escape_and_create_quotes` | `(text: str, strict: bool)` |  |
| method | `Markdown.parse` | `(cls, text: str, strict: bool=False)` |  |
| method | `Markdown.unparse` | `(text: str, entities: list)` |  |
| func | `parse_text` | `(text: str, parse_mode: Optional[str]='HTML', is_caption: bool=False)` |  |

### `ui/__init__.py` (1 строк)

### `ui/alert.py` (352 строк)

Java/Android-зависимости: `android.content`, `android.graphics.drawable`, `android.view`, `android.widget`, `java`, `java.lang.ref`, `org.telegram.ui.ActionBar`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `AlertDialogBuilder` | `` |  |
| const | `AlertDialogBuilder.ALERT_TYPE_MESSAGE` | `= 0` |  |
| const | `AlertDialogBuilder.ALERT_TYPE_LOADING` | `= 2` |  |
| const | `AlertDialogBuilder.ALERT_TYPE_SPINNER` | `= 3` |  |
| const | `AlertDialogBuilder.BUTTON_POSITIVE` | `= -1` |  |
| const | `AlertDialogBuilder.BUTTON_NEGATIVE` | `= -2` |  |
| const | `AlertDialogBuilder.BUTTON_NEUTRAL` | `= -3` |  |
| method | `AlertDialogBuilder.__init__` | `(self, context: Context, progress_style: int=ALERT_TYPE_MESSAGE, resources_provider: Optional[Theme.ResourcesProvider]=None)` |  |
| method | `AlertDialogBuilder.get_context` | `(self)` | Returns the context used by this builder. |
| method | `AlertDialogBuilder.set_title` | `(self, title: str)` | Sets the title of the dialog. |
| method | `AlertDialogBuilder.set_message` | `(self, message: str)` | Sets the message content of the dialog. |
| method | `AlertDialogBuilder.set_message_text_view_clickable` | `(self, clickable: bool)` | Sets whether the message TextView is clickable (e.g., for links). |
| method | `AlertDialogBuilder.set_positive_button` | `(self, text: str, listener: Optional[Callable[['AlertDialogBuilder', int], None]]=None)` | Sets the positive button text and its click listener. |
| method | `AlertDialogBuilder.set_negative_button` | `(self, text: str, listener: Optional[Callable[['AlertDialogBuilder', int], None]]=None)` | Sets the negative button text and its click listener. |
| method | `AlertDialogBuilder.set_neutral_button` | `(self, text: str, listener: Optional[Callable[['AlertDialogBuilder', int], None]]=None)` | Sets the neutral button text and its click listener. |
| method | `AlertDialogBuilder.make_button_red` | `(self, button_type: int)` | Marks a button to be styled with red text after the dialog is shown. Use `AlertDialogBuilder.BUTTON_POSITIVE`, `BUTTON_NEGATIVE`, or `BUTTON_NEUTRAL`. |
| method | `AlertDialogBuilder.set_on_back_button_listener` | `(self, listener: Optional[Callable[['AlertDialogBuilder', int], None]]=None)` | Sets a listener for when the back button is pressed while the dialog is showing. |
| method | `AlertDialogBuilder.set_view` | `(self, view: View, height: int=-2)` | Sets a custom view for the dialog. |
| method | `AlertDialogBuilder.set_items` | `(self, items: List[str], listener: Optional[Callable[['AlertDialogBuilder', int], None]]=None, icons: Optional[List[int]]=None)` | Sets a list of items to be displayed in the dialog. |
| method | `AlertDialogBuilder.set_on_dismiss_listener` | `(self, listener: Optional[Callable[['AlertDialogBuilder'], None]]=None)` | Sets a listener to be invoked when the dialog is dismissed. |
| method | `AlertDialogBuilder.set_on_cancel_listener` | `(self, listener: Optional[Callable[['AlertDialogBuilder'], None]]=None)` | Sets a listener to be invoked when the dialog is cancelled. |
| method | `AlertDialogBuilder.set_top_image` | `(self, res_id: int, background_color: int)` | Sets an image resource at the top of the dialog. |
| method | `AlertDialogBuilder.set_top_drawable` | `(self, drawable: Drawable, background_color: int)` | Sets a drawable at the top of the dialog. |
| method | `AlertDialogBuilder.set_top_animation` | `(self, res_id: int, size: int, auto_repeat: bool, background_color: int, layer_colors: Optional[Dict[str, int]]=None)` | Sets an animation at the top of the dialog. |
| method | `AlertDialogBuilder.set_top_animation_is_new` | `(self, is_new: bool)` | Configures the style of the top animation area. |
| method | `AlertDialogBuilder.set_dim_enabled` | `(self, enabled: bool)` | Enable or disable dimming of the background behind the dialog. |
| method | `AlertDialogBuilder.set_dialog_button_color_key` | `(self, theme_key: int)` | Sets the theme color key for dialog buttons. |
| method | `AlertDialogBuilder.set_blurred_background` | `(self, blur: bool, blur_behind_if_possible: bool=True)` | Tries to set a blurred background for the dialog. Actual blurring depends on device capabilities. |
| method | `AlertDialogBuilder.create` | `(self)` | Creates the AlertDialog but does not show it. Call show() to display. |
| method | `AlertDialogBuilder.show` | `(self)` | Creates and shows the AlertDialog. |
| method | `AlertDialogBuilder.dismiss` | `(self)` | Dismisses the dialog if it's showing. |
| method | `AlertDialogBuilder.get_dialog` | `(self)` | Returns the underlying Java AlertDialog instance, if created. |
| method | `AlertDialogBuilder.get_button` | `(self, button_type: int)` | Gets a button view from the dialog. Call this after create() or show(). Use `AlertDialogBuilder.BUTTON_POSITIVE`, etc. |
| method | `AlertDialogBuilder.set_progress` | `(self, progress: int)` | Sets the progress for ALERT_TYPE_LOADING style dialogs. |
| method | `AlertDialogBuilder.set_cancelable` | `(self, cancelable: bool)` | Sets whether the dialog is cancelable. |
| method | `AlertDialogBuilder.set_canceled_on_touch_outside` | `(self, cancel: bool)` | Sets whether the dialog is canceled when touched outside its window's bounds. |

### `ui/bulletin.py` (254 строк)

Java/Android-зависимости: `org.telegram.messenger`, `org.telegram.ui.ActionBar`, `org.telegram.ui.Components`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `BulletinHelper` | `` | A helper class to easily show various types of Bulletins from Python. Wraps common functionalities of org.telegram.ui.Components.BulletinFactory. |
| const | `BulletinHelper.DURATION_SHORT` | `= 1500` |  |
| const | `BulletinHelper.DURATION_LONG` | `= 2750` |  |
| const | `BulletinHelper.DURATION_PROLONG` | `= 5000` |  |
| method | `BulletinHelper.show_info` | `(cls, message: str, fragment: Optional[BaseFragment]=None)` | Shows a simple informational bulletin with a default info icon. |
| method | `BulletinHelper.show_error` | `(cls, message: str, fragment: Optional[BaseFragment]=None)` | Shows an error bulletin with a default error icon. |
| method | `BulletinHelper.show_success` | `(cls, message: str, fragment: Optional[BaseFragment]=None)` | Shows a success bulletin with a default success/check icon. |
| method | `BulletinHelper.show_simple` | `(cls, text: str, icon_res_id: int, fragment: Optional[BaseFragment]=None)` | Shows a bulletin with a custom icon and a single line of text. :param text: The message to display. :param icon_res_id: The R.raw.xxx resource ID for the Lottie animation. :param fragment: Optional BaseFragment to attach |
| method | `BulletinHelper.show_two_line` | `(cls, title: str, subtitle: str, icon_res_id: int, fragment: Optional[BaseFragment]=None)` | Shows a bulletin with a custom icon, a title, and a subtitle. :param title: The main text (title). :param subtitle: The secondary text (subtitle). :param icon_res_id: The R.raw.xxx resource ID for the Lottie animation. : |
| method | `BulletinHelper.show_with_button` | `(cls, text: str, icon_res_id: int, button_text: str, on_click: Optional[Callable[[], None]], fragment: Optional[BaseFragment]=None, duration: int=DURATION_PR...` | Shows a bulletin with an icon, text, and a button. :param text: The main message. :param icon_res_id: The R.raw.xxx resource ID for the Lottie animation. Can be 0 for no icon. :param button_text: Text for the button. :pa |
| method | `BulletinHelper.show_undo` | `(cls, text: str, on_undo: Callable[[], None], on_action: Optional[Callable[[], None]]=None, subtitle: Optional[str]=None, fragment: Optional[BaseFragment]=None)` | Shows an undo-style bulletin. :param text: The main message. :param on_undo: Callable executed if the "Undo" button is pressed. :param on_action: Callable executed after a delay if "Undo" is not pressed. :param subtitle: |
| method | `BulletinHelper.show_copied_to_clipboard` | `(cls, message: Optional[str]=None, fragment: Optional[BaseFragment]=None)` | Shows a "Copied to clipboard" bulletin. |
| method | `BulletinHelper.show_link_copied` | `(cls, is_private_link_info: bool=False, fragment: Optional[BaseFragment]=None)` | Shows a "Link copied" bulletin. |
| method | `BulletinHelper.show_file_saved_to_gallery` | `(cls, is_video: bool=False, amount: int=1, fragment: Optional[BaseFragment]=None)` | Shows "Photo/Video saved to gallery" or plural version. |
| method | `BulletinHelper.show_file_saved_to_downloads` | `(cls, file_type_enum_name: str='UNKNOWN', amount: int=1, fragment: Optional[BaseFragment]=None)` | Shows "File saved to downloads" or similar, based on FileType enum. :param file_type_enum_name: String name of the enum from BulletinFactory.FileType (e.g., "UNKNOWN", "PHOTO_TO_DOWNLOADS"). :param amount: Number of file |

### `ui/settings.py` (363 строк)

Java/Android-зависимости: `android.view`, `com.android.dx`, `com.chaquo.python`, `com.exteragram.messenger.plugins`, `com.exteragram.messenger.plugins.models`, `com.exteragram.messenger.plugins.utils`, `java`, `java.lang`, `java.lang.reflect`, `org.telegram.ui.Components`

| Вид | Имя | Сигнатура | Описание (docstring) |
|---|---|---|---|
| class | `Switch` | `` |  |
| field | `Switch.key` | `: str` |  |
| field | `Switch.text` | `: str` |  |
| field | `Switch.default` | `: bool` |  |
| field | `Switch.subtext` | `: str = None` |  |
| field | `Switch.icon` | `: str = None` |  |
| field | `Switch.on_change` | `: Callable[[bool], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Switch.type` | `: str = field(default=PluginsConstants.Settings.TYPE_SWITC` |  |
| field | `Switch.on_long_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Switch.link_alias` | `: str = None` |  |
| class | `Selector` | `` |  |
| field | `Selector.key` | `: str` |  |
| field | `Selector.text` | `: str` |  |
| field | `Selector.default` | `: int` |  |
| field | `Selector.items` | `: List[str]` |  |
| field | `Selector.icon` | `: str = None` |  |
| field | `Selector.on_change` | `: Callable[[int], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Selector.type` | `: str = field(default=PluginsConstants.Settings.TYPE_SELEC` |  |
| field | `Selector.on_long_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Selector.link_alias` | `: str = None` |  |
| class | `Input` | `` |  |
| field | `Input.key` | `: str` |  |
| field | `Input.text` | `: str` |  |
| field | `Input.default` | `: str = ''` |  |
| field | `Input.subtext` | `: str = None` |  |
| field | `Input.icon` | `: str = None` |  |
| field | `Input.on_change` | `: Callable[[str], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Input.type` | `: str = field(default=PluginsConstants.Settings.TYPE_INPUT` |  |
| field | `Input.on_long_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Input.link_alias` | `: str = None` |  |
| class | `Text` | `` |  |
| field | `Text.text` | `: str` |  |
| field | `Text.subtext` | `: str = None` |  |
| field | `Text.icon` | `: str = None` |  |
| field | `Text.accent` | `: bool = False` |  |
| field | `Text.red` | `: bool = False` |  |
| field | `Text.on_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Text.create_sub_fragment` | `: Callable[[], List[Any]] = field(default=None, compare=False, repr=False)` |  |
| field | `Text.type` | `: str = field(default=PluginsConstants.Settings.TYPE_TEXT,` |  |
| field | `Text.on_long_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Text.link_alias` | `: str = None` |  |
| class | `Header` | `` |  |
| field | `Header.text` | `: str` |  |
| field | `Header.type` | `: str = field(default=PluginsConstants.Settings.TYPE_HEADE` |  |
| class | `Divider` | `` |  |
| field | `Divider.text` | `: str = None` |  |
| field | `Divider.type` | `: str = field(default=PluginsConstants.Settings.TYPE_DIVID` |  |
| class | `EditText` | `` |  |
| field | `EditText.key` | `: str` |  |
| field | `EditText.hint` | `: str` |  |
| field | `EditText.default` | `: str = ''` |  |
| field | `EditText.multiline` | `: bool = False` |  |
| field | `EditText.max_length` | `: int = 256` |  |
| field | `EditText.mask` | `: str = None` |  |
| field | `EditText.on_change` | `: Callable[[str], None] = field(default=None, compare=False, repr=False)` |  |
| field | `EditText.type` | `: str = field(default=PluginsConstants.Settings.TYPE_EDIT_` |  |
| class | `Custom` | `` |  |
| field | `Custom.type` | `: str = field(default=PluginsConstants.Settings.TYPE_CUSTO` |  |
| field | `Custom.item` | `: UItem = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.view` | `: View = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.factory` | `: CustomSetting.Factory = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.factory_args` | `: Any = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.on_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.on_long_click` | `: Callable[[View], None] = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.create_sub_fragment` | `: Callable[[], List[Any]] = field(default=None, compare=False, repr=False)` |  |
| field | `Custom.link_alias` | `: str = None` |  |
| class | `SimpleSettingFactory` | `` |  |
| method | `SimpleSettingFactory.__init__` | `(self, create_view: callable, bind_view: callable, *, is_clickable: bool=False, is_shadow: bool=False, create_item: Optional[callable]=None, on_click: Option...` |  |
| method | `SimpleSettingFactory.release` | `(self)` |  |

