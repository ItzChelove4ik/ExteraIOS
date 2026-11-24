# Инвентаризация exteraGram (Android) для порта на iOS

Источник: `exteraSquad/exteraGram@b4d852f4` (13.2.2), только чтение. Документ сгенерирован скриптом из исходников: ключ, тип, значение по умолчанию, место в интерфейсе и файлы, где ключ используется. Колонки «Что делает», «iOS», «Как / почему» и «Аналог» заполнены вручную по коду и строкам локализации.

Обозначения: ✅ переносится как есть · ⚠️ переносится с адаптацией · ❌ невозможно или бессмысленно на iOS · ❓ нужно уточнить по коду до решения.
«Аналог»: `SG:ключ` — настройка Swiftgram (`SGSimpleSettings`), `TG` — есть в стоковом Telegram-iOS, «—» — аналога нет.

## Сводка

| | Количество ключей |
|---|---|
| ✅ | 59 |
| ⚠️ | 88 |
| ❓ | 12 |
| ❌ | 17 |
| **Всего ключей `ExteraConfig.kt`** | **176** |

- Своих Kotlin/Java-файлов exteraGram в `com/exteragram/messenger/`: 484; файлов `org.telegram.*`, где упоминается exteraGram или `ExteraConfig`: 325 (полный список в конце).
- Строк локализации: 12873 всего, из них 1334 в `extera.xml`.
- Колонка «Android: где используется» найдена поиском по имени свойства и его Java-геттерам (`getX`/`isX`/`setX`). Это эвристика: у общих имён (`titleText`, `radius`) бывают ложные совпадения.

## 1. Настройки `ExteraConfig.kt`

### General

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `translationProvider` | Integer | `0` | Провайдер перевода сообщений: Google, Microsoft, Yandex, Telegram | Основные / Translate Messages → «Translation Provider» | `TranslateAlert2.java`; exteragram: `TranslationProviders.kt` | ⚠️ | в Swiftgram свой выбор бэкенда, нужно добавить провайдеров Microsoft и Yandex | SG:translationBackend (частично) |
| `disableNumberRounding` | Boolean | `false` | Не сокращать числа: 1.23K → 1,234 | Основные / General → «Disable Number Rounding» | `LocaleController.java` | ✅ |  | — |
| `formatTimeWithSeconds` | Boolean | `false` | Время с секундами | Основные / General → «Format Time with Seconds» | `LocaleController.java` | ✅ |  | SG:secondsInMessages (только в сообщениях) |
| `relativeLastSeen` | Boolean | `false` | «Был(а) в сети» в относительном виде | Основные / Profile → «Relative Last Seen» | `LocaleController.java` | ✅ |  | — |
| `inAppVibration` | Boolean | `true` | Вибрация внутри приложения | Основные / General → «In-App Vibration» | `AndroidUtilities.java`, `BotWebViewVibrationEffect.java`, `ActionBarLayout.java`, `BottomSheet.java` +2; exteragram: `VibratorUtils.java`, `SliderHapticsHelper.java` | ⚠️ | на iOS это haptic feedback (UIFeedbackGenerator), выключать в местах вызова | — |
| `disableNotificationDelay` | Boolean | `false` | Отключить задержку уведомлений | Основные / General → «Disable Notification Delay» | `NotificationsController.java` | ❓ | на Android это задержка показа, когда приложение открыто. На iOS уведомления устроены иначе, нужно сравнить с кодом Telegram-iOS | — |
| `filterZalgo` | Boolean | `true` | Фильтр Zalgo-текста (нагромождение диакритики) | Основные / General → «Filter \"Zalgo\"» | exteragram: `ZalgoFilter.java` | ✅ | чистая логика над строками | — |
| `downloadSpeedBoost` | Integer | `0` | Ускорение загрузки: выкл / быстро / ультра |  | `FileLoadOperation.java` | ✅ |  | SG:downloadSpeedBoost (совпадает) |
| `uploadSpeedBoost` | Boolean | `false` | Ускорение отправки файлов | Основные / Download Speed Boost → «Upload Speed Boost» | `FileUploadOperation.java` | ✅ |  | SG:uploadSpeedBoost (совпадает) |
| `hidePhoneNumber` | Boolean | `false` | Скрыть свой номер телефона | Основные / Profile → «Hide Phone Number» | `ProfileSearchCell.java`, `ProfileActivity.java`, `SettingsActivity.java`; exteragram: `DrawerHeaderView.java` | ✅ |  | SG:hidePhoneInSettings (частично) |
| `showIdAndDc` | Integer | `1` | Показывать ID и дата-центр в профиле (варианты) | Основные / Profile → «Show ID and DC» | `PhotoViewer.java`, `ProfileActivity.java` | ✅ |  | SG:showProfileId + SG:showDC (совпадает) |
| `defaultProfileTab` | Enum | `DefaultProfileTab.DEFAULT` | Вкладка профиля по умолчанию: медиа / общие группы | Основные / Profile → «Default Tab» | exteragram: `ProfileUiHelper.java` | ✅ |  | — |
| `hideArchiveFolder` | Boolean | `false` | Скрыть папку «Архив» в списке чатов | Основные / Archived Chats → «Hide Archive Folder» | `MessagesController.java` | ✅ |  | — (в TG архив можно только свернуть) |
| `archiveOnPull` | Boolean | `false` | Открывать архив свайпом вниз по списку чатов | Основные / Archived Chats → «Open Archive on Pull-down» | `DialogsActivity.java` | ⚠️ | жест в ChatListController | — |
| `disableUnarchiveSwipe` | Boolean | `true` | Отключить свайп «Разархивировать» | Основные / Archived Chats → «Disable \"Unarchive\" Swipe» | `DialogsActivity.java` | ✅ |  | SG:disableChatSwipeOptions (частично) |
| `doNotUseProxy` | Integer | `0` | Не использовать прокси при VPN / мобильной сети / Wi-Fi (битовая маска) |  | — | ⚠️ | Wi-Fi/сотовая — NWPathMonitor; определение VPN на iOS только неофициально (интерфейсы utun/ipsec) | — |
| `customSavePath` | String | `"exteraGram"` | Своя папка для сохранения файлов | Основные / Storage → «Custom Save Folder» | `MediaController.java`; exteragram: `ExportFiles.java` | ❌ | на iOS нет общей файловой системы; замена — «Сохранить в Файлы» с выбором папки (UIDocumentPicker) | — |

### Icon Packs

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `iconPack` | Enum | `IconPackType.DEFAULT` | Набор иконок интерфейса: стандартный / Solar / Remix |  | exteragram: `BlendedReplySpans.kt`, `IconManager.kt` +7 | ⚠️ | нужны ассеты под iOS (Images.xcassets Telegram-iOS); иконки Solar/Remix — проверить лицензии | — |
| `editingIconPackId` | NullableString | `null` | Служебное: редактируемый набор иконок |  | exteragram: `IconManager.kt`, `IconPacksActivity.kt` +5 | ⚠️ | вместе с iconPack | — |

### Appearance

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `avatarCorners` | Float | `28.0f` | Скругление аватарок (0–28) |  | `ChatsWidgetService.java`, `ContactsWidgetService.java`, `ActionBarMenuItem.java`, `FiltersView.java` +103; exteragram: `CatalogRepositoryCell.kt`, `DrawerAccountPickerView.java` +3 | ⚠️ | аватарки рисуются во многих местах (AvatarNode и др.), нужна единая точка | — |
| `singleCornerRadius` | Boolean | `false` | Одинаковое скругление для аватарок форумов и сообществ | Оформление → «Single Corner Radius» | — | ⚠️ | вместе с avatarCorners | — |
| `dividerStyle` | Enum | `DividerStyle.LINE` | Стиль разделителей: нет / линия / сегменты | Оформление / Sections → «Divider Style» | `AndroidUtilities.java`, `Theme.java`, `ChatMessagePoll.java`, `DividerCell.java` +2; exteragram: `WebAppSectionStyle.kt` | ⚠️ | ItemListUI и списки | — |
| `forceSnow` | Boolean | `false` | Принудительный снег | Оформление / Chat List → «Force Snowflakes» | `Theme.java` | ✅ |  | SG:nyStyle (snow) (совпадает) |
| `hideActionBarStatus` | Boolean | `false` | Скрыть статус в шапке списка чатов | Оформление / Chat List → «Hide Status» | `ActionBar.java`, `DialogStoriesCell.java` | ✅ |  | — |
| `centerTitle` | Boolean | `false` | Заголовок по центру | Оформление / Chat List → «Center Title» | `ActionBar.java`, `ActionBarMenuItem.java`, `SimpleActionBar.java`, `PhotoViewerWebView.java` +2 | ❌ | на iOS заголовок навбара и так по центру | TG (по умолчанию) |
| `hideStories` | Boolean | `false` | Скрыть истории | Оформление / Chat List → «Hide Stories» | `MessagesController.java`, `DialogsActivity.java`, `ProfileActivity.java`, `StoriesController.java` +1 | ✅ |  | SG:hideStories (совпадает) |
| `hideFloatingButton` | Boolean | `false` | Скрыть плавающую кнопку (FAB) | Оформление / Chat List → «Hide Floating Button» | `DialogsAdapter.java`, `DialogsEmptyCell.java`, `DialogsActivity.java`, `TopicsFragment.java` | ❌ | в iOS нет FAB, кнопка «написать» в навбаре | — |
| `hideDialogsSearchBar` | Boolean | `false` | Скрыть строку поиска в списке чатов | Оформление / Chat List → «Hide Search Bar» | `DialogsActivity.java` | ⚠️ |  | — |
| `senderMiniAvatars` | Boolean | `true` | Мини-аватар отправителя в превью сообщения в списке чатов | Оформление / Chat List → «Sender Mini Avatars» | `DialogCell.java` | ⚠️ | ChatListItem | — |
| `titleText` | Integer | `0` | Текст заголовка списка чатов (варианты) | Оформление / Chat List → «Title Text» | `ChatActivity.java`, `ItemOptions.java`, `TopicsSidePanel.java`, `StarsReactionsSheet.java` +1; exteragram: `AnalyzerUpdateAlert.kt`, `InstallPluginBottomSheet.kt` +3 | ⚠️ | шапка ChatListController; совпадения в коде частично ложные (общее имя) | — |
| `tabIcons` | Enum | `TITLES_ONLY` | Папки: иконки и названия / только названия / только иконки | Оформление / Folders → «Folder Title» | `EmojiView.java`, `FilterTabsView.java`, `DialogsActivity.java`, `QrShareView.java` +1 | ⚠️ | в Telegram-iOS у папок есть иконки, нужна проверка | SG:compactFolderNames (частично) |
| `tabCounterMode` | Enum | `TabCounterMode.ALL` | Счётчик у папок: все / без заглушённых / скрыт | Оформление / Folders → «Notification Counter» | `DialogsActivity.java`; exteragram: `FolderCounters.kt` | ⚠️ |  | — |
| `hideAllChats` | Boolean | `false` | Скрыть вкладку «Все чаты» | Оформление / Folders → «Hide \"%1$s\" Tab» | `FilterTabsView.java`, `DialogsActivity.java`, `MainTabsActivity.java` | ✅ |  | SG:allChatsHidden (совпадает) |
| `squareFab` | Boolean | `true` | Квадратная FAB |  | `MediaDataController.java`, `FragmentFloatingButton.java`, `LoginActivity.java`, `PhotoAlbumPickerActivity.java` +2; exteragram: `FabUiHelper.java`, `UIUtil.kt` | ❌ | в iOS нет FAB | — |
| `sectionRadius` | Float | `DEFAULT_SECTION_RADIUS_DP.toFloat(` | Радиус скругления секций настроек |  | `RecyclerListView.java`, `SectionsScrollView.java` | ⚠️ | ItemListUI (insetGrouped) | — |
| `sectionsSeparatedHeadersPreference` | Boolean | `true, "sectionsSeparatedHeaders"` | Заголовки секций отдельно от блоков | Оформление / Sections → «Separate Headers» | — | ⚠️ | ItemListUI | — |
| `newLoadingStyle` | Boolean | `true` | Новый стиль индикатора загрузки |  | `AlertDialog.java`, `CircularProgressDrawable.java`, `LineProgressView.java`, `RadialProgress2.java` +2; exteragram: `ExportProgressSheet.java` | ❌ | Android-контролы (Material); на iOS системные | — |
| `newSliderStyle` | Boolean | `true` | Новый стиль слайдеров |  | `SeekBarView.java`, `SlideChooseView.java`, `PhotoViewer.java` | ❌ | Android-контролы | — |
| `newSwitchStyle` | Boolean | `true` | Новый стиль переключателей |  | exteragram: `SwitchUiHelper.java` | ❌ | Android-контролы, на iOS UISwitch | — |
| `newChatHeaderStyle` | Boolean | `false` | Новый стиль шапки чата |  | `ActionBar.java`; exteragram: `FeedActivity.java`, `ChatHeaderUiHelper.java` | ❓ | нужно разобрать, что меняется визуально | — |
| `newNavigationBarStyle` | Boolean | `false` | Новый стиль нижней навигации |  | exteragram: `MainTabsUiHelper.java` | ⚠️ | TabBar | SG:bottomTabStyle / SG:wideTabBar (частично) |
| `newFabStyle` | Boolean | `false` | Новый стиль FAB |  | exteragram: `FabUiHelper.java` | ❌ | в iOS нет FAB | — |
| `newProfileActionsStyle` | Boolean | `false` | Новый стиль кнопок действий в профиле |  | exteragram: `ProfileUiHelper.java` | ⚠️ | в iOS-профиле уже есть кнопки действий; сравнить | TG (своя реализация) |
| `newPlayerStyle` | Boolean | `false` | Новый музыкальный плеер |  | `MediaController.java`, `ChatMessageCell.java`, `FragmentContextView.java`; exteragram: `PlayerLauncher.java`, `SpeedPitchMenuItem.java` | ⚠️ | пакет player — 18,9 тыс. строк, на iOS писать заново поверх OverlayAudioPlayer/MediaPlayer | — |
| `playerCoverColors` | Boolean | `false` | Плеер: цвета из обложки |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | часть нового плеера | — |
| `playerMiniCoverColors` | Boolean | `false` | Мини-плеер: цвета из обложки |  | exteragram: `PlayerColors.java`, `MiniPlayerUiHelper.java` +1 | ⚠️ | часть нового плеера | — |
| `lyricsOnline` | Boolean | `false` | Тексты песен из интернета |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | внешние сервисы (lrclib.net и др.) — вопрос разрешения | — |
| `lyricsProviders` | StringSet | `setOf("lrclib", "lrcmux"` | Провайдеры текстов: lrclib, lrcmux |  | exteragram: `LyricsProvider.java`, `PlayerSettingsSheet.java` | ⚠️ | внешние сервисы | — |
| `lyricsProgress` | Integer | `1` | Режим подсветки строки текста |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | часть плеера | — |
| `lyricsSubtitle` | Integer | `1` | Вид подстрочника текста |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | часть плеера | — |
| `playerMotionCovers` | Boolean | `false` | Анимированные (видео) обложки |  | exteragram: `MusicPlayerSheet.java`, `MotionCoverRepository.java` +1 | ⚠️ | внешний источник (Apple Music) — вопрос | — |
| `playerSpotifyCanvas` | Boolean | `false` | Spotify Canvas — фоновое видео трека |  | exteragram: `CanvasRepository.java`, `PlayerSettingsSheet.java` | ⚠️ | неофициальное API Spotify (spclient.wg.spotify.com) — вопрос | — |
| `playerYandexCanvas` | Boolean | `false` | Yandex Music Canvas |  | exteragram: `CanvasRepository.java`, `PlayerSettingsSheet.java` | ⚠️ | неофициальное API — вопрос | — |
| `playerRhythmBackground` | Boolean | `true` | Фон плеера в ритм музыке |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | анализ аудио (AVAudioEngine tap / Accelerate) | — |
| `playerParticles` | Boolean | `false` | Частицы в плеере |  | exteragram: `MusicPlayerSheet.java`, `PlayerSettingsSheet.java` | ⚠️ | Metal / CAEmitterLayer | — |
| `playerSpeedPitch` | Boolean | `false` | Скорость и тон в плеере |  | `MediaController.java`; exteragram: `MusicPlayerSheet.java`, `SpeedPitchMenuItem.java` | ⚠️ | AVAudioUnitTimePitch; у Telegram-iOS свой аудиоплеер | TG (скорость есть, тона нет) |
| `playerMode` | Integer | `0` | Режим плеера |  | exteragram: `MusicPlayerSheet.java` | ❓ | уточнить значения | — |
| `tabletMode` | Integer | `0` | Планшетный режим (авто / вкл / выкл) | Оформление → Навигация / General → «Tablet Mode» | `AndroidUtilities.java`, `GroupCallActivity.java` | ⚠️ | на iPad в Telegram-iOS уже есть двухпанельный режим, оставить только настройку | TG (iPad split) |
| `tabletLeftFraction` | Float | `0.35f` | Ширина левой панели в планшетном режиме |  | exteragram: `TabletSplitUiHelper.java` | ⚠️ | iPad split | — |
| `useSystemFonts` | Boolean | `true` | Системный шрифт вместо Roboto | Оформление / Appearance → «Use System Fonts» | `AndroidUtilities.java` | ❌ | на iOS шрифт и так системный (SF) | TG |
| `gooeyAvatarAnimation` | Boolean | `true` | «Липкая» анимация аватара в профиле | Оформление / Appearance → «\"Gooey\" Avatar Animation» | `ProfileActivity.java`, `SettingsActivity.java` | ⚠️ | у iOS-профиля своя анимация; переносить по кадрам (AGENTS.md) | — |
| `customThemes` | Boolean | `true` | Темы чатов (custom themes) в чатах | Оформление / Appearance → «Custom Themes in Chats» | `ChatThemeController.java`, `ChatActivity.java` | ❓ | уточнить, что именно отключается | TG (темы чатов) |
| `predictiveBackIntensity` | Float | `1.0f` | Сила анимации predictive back |  | exteragram: `PredictiveBackAnimationHelper.java` | ❌ | жест Android 14 | — |
| `transitionAnimation` | Enum | `TransitionAnimation.SPRING` | Анимация переходов: стандартная / AOSP / пружинная | Оформление → Навигация / General → «Transition Animation» | — | ❌ | Android-переходы; на iOS системный push | — |

### Blur Preferences

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `glassOutlineStyle` | Enum | `GlassOutlineStyle.GLARE` | Контур «стекла»: блик / сплошной / нет | Оформление / Blur Options → «Glass Outline» | `PasscodeView.java`, `StrokeDrawable.java`, `BlurredBackgroundDrawable.java`, `QrGlass.java` +2; exteragram: `GlassUiHelper.java` | ⚠️ | в Telegram-iOS 13.x уже есть Liquid Glass (iOS 26+), соотнести | TG (Liquid Glass) |
| `glassMessageMenu` | Boolean | `true` | Стеклянное контекстное меню сообщения | Оформление / Blur Options → «Glass Message Menu» | exteragram: `GlassMenuHelper.java` | ⚠️ | соотнести с Liquid Glass в TG-iOS | TG (Liquid Glass) |
| `headerBlurStyle` | Enum | `HeaderBlurStyle.PROGRESSIVE` | Размытие шапки: обычное / прогрессивное / затухание | Оформление / Blur Options → «Header Blur» | `BaseFragmentSimpleGlass.java` | ⚠️ | NavigationBar | — |

### Event icon style

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `eventType` | Integer | `0` | Праздничный стиль иконок (Новый год и т. п.) |  | `AndroidUtilities.java`, `LocaleController.java`, `Theme.java`, `ChatMessageCell.java` +2; exteragram: `PluginsController.kt`, `PythonPluginsEngine.kt` +1 | ⚠️ |  | SG:nyStyle (частично) |
| `navigationDrawer` | Boolean | `false` | Боковое меню (drawer) вместо вкладок | Оформление → Навигация / App Navigation → «Navigation Drawer» | `ActionBar.java`, `DialogsActivity.java`, `LaunchActivity.java`; exteragram: `DrawerContainer.java` | ⚠️ | для iOS нетипично, реализуемо как отдельный экран — спросить | — |
| `immersiveDrawerAnimation` | Boolean | `false` | Иммерсивная анимация бокового меню | Оформление → Навигация / App Navigation → «Immersive Animation» | exteragram: `DrawerContainer.java` | ⚠️ | вместе с navigationDrawer | — |
| `hideNavigationBarLabels` | Boolean | `false` | Скрыть подписи нижней панели | Оформление → Навигация / General → «Hide Labels» | `GlassTabView.java`; exteragram: `MainTabsUiHelper.java` | ✅ |  | SG:showTabNames (совпадает) |
| `showFeedTab` | Boolean | `false` | Вкладка «Лента» (посты каналов) вместо «Контактов» |  | `MainTabsActivity.java`; exteragram: `FeedChannelsActivity.kt` | ⚠️ | пакет feed — 8,3 тыс. строк, новый экран на iOS | — |
| `showFeedUnreadCounter` | Boolean | `true` | Счётчик непрочитанных у ленты |  | exteragram: `FeedController.java`, `FeedChannelsActivity.kt` | ⚠️ | часть feed | — |

### Chats

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `stickerSize` | Float | `12.0f` | Размер стикеров |  | `ChatActionCell.java`, `ChatMessageCell.java`, `PhotoViewer.java` | ✅ |  | SG:stickerSize (совпадает) |
| `stickerTimeMode` | Enum | `StickerTimeMode.DEFAULT` | Время на стикерах: обычно / сбоку / скрыто | Чаты → «Time on Stickers» | exteragram: `StickerTime.java` | ✅ |  | SG:stickerTimestamp (частично) |
| `replyColors` | Boolean | `true` | Цвет имени в цитате ответа |  | `ReplyMessageLine.java` | ⚠️ | ChatMessageReplyInfoNode | — |
| `replyEmoji` | Boolean | `true` | Эмодзи-фон (профильный) в цитате ответа |  | `ChatActivity.java`, `ReplyMessageLine.java` | ⚠️ |  | — |
| `replyBackground` | Boolean | `true` | Фон цитаты ответа |  | `ReplyMessageLine.java` | ⚠️ |  | — |
| `stickerShape` | Integer | `1` | Форма стикеров (секция «Форма стикера») |  | `ChatMessageCell.java`, `StickerCell.java`, `StickerEmojiCell.java` | ❓ | уточнить варианты | — |
| `unlimitedRecentStickers` | Boolean | `false` | Неограниченные недавние стикеры | Чаты / Stickers → «Unlimited Recent Stickers» | `MediaDataController.java` | ✅ |  | — |
| `hideReactionsInPrivateChats` | Boolean | `` | Скрыть реакции в личных чатах |  | `DialogCell.java`, `ChatActivity.java`, `ReactionsEffectOverlay.java`, `ReactionsLayoutInBubble.java` | ✅ |  | SG:hideReactions (глобально, частично) |
| `hideReactionsInChannels` | Boolean | `false` | Скрыть реакции в каналах |  | `DialogCell.java`, `ChatActivity.java`, `ReactionsEffectOverlay.java`, `ReactionsLayoutInBubble.java` | ✅ |  | SG:hideReactions (частично) |
| `hideReactionsInGroups` | Boolean | `false` | Скрыть реакции в группах |  | `DialogCell.java`, `ChatActivity.java`, `ReactionsEffectOverlay.java`, `ReactionsLayoutInBubble.java` | ✅ |  | SG:hideReactions (частично) |
| `doubleTapAction` | SanitizedInteger | `1` | Двойной тап по входящим сообщениям | Чаты / Gestures → «Incoming Messages» | `ChatActivity.java` | ✅ |  | TG (быстрая реакция) + SGDoubleTapMessageAction (частично) |
| `doubleTapActionOutOwner` | SanitizedInteger | `1` | Двойной тап по своим сообщениям | Чаты / Gestures → «Outgoing Messages» | `ChatActivity.java` | ✅ |  | SG:messageDoubleTapActionOutgoing (совпадает) |
| `swipeActions` | String | `DoubleTapUtils.ACTION_REPLY.toString(` | Действия по свайпу сообщения (ответ и др.) | Чаты / Gestures → «Swipe Actions» | exteragram: `SwipeAction.java` | ⚠️ | жест в ChatMessageBubbleItemNode | — |
| `swipeActionsLoop` | Boolean | `false` | Свайп-действия по кругу | Чаты → Свайп-действия / Behavior → «Loop Actions» | exteragram: `SwipeActionsHelper.java` | ⚠️ |  | — |
| `swipeActionsReversed` | Boolean | `false` | Обратная прокрутка свайп-действий | Чаты → Свайп-действия / Behavior → «Reverse Scrolling» | exteragram: `SwipeActionsHelper.java` | ⚠️ |  | — |
| `bottomButton` | Integer | `2` | Нижняя кнопка в канале (заглушить / обсуждение / скрыть) | Чаты / Chats → «Bottom Button» | `ChatActivity.java`, `ProfileActivity.java`, `VoIPFragment.java`, `CommunitySheet.java` | ✅ |  | SG:hideChannelBottomButton (частично) |
| `widePostsInFeed` | Boolean | `true` | Широкие посты в ленте |  | `ChatActivity.java`; exteragram: `FeedChannelsActivity.kt`, `WidePosts.java` | ⚠️ | часть feed | — |
| `widePostsInChannels` | Boolean | `false` | Широкие посты в каналах |  | `ChatActivity.java`, `LaunchActivity.java`; exteragram: `WidePosts.java` | ✅ |  | SG:wideChannelPosts (совпадает) |
| `telegramAiEditor` | Boolean | `true` | Показывать AI-редактор Telegram |  | `CaptionPhotoViewer.java`, `ChatActivityEnterView.java`, `ChatAttachAlert.java`, `LinkManager.java` +2 | ❓ | проверить, есть ли эта функция в Telegram-iOS 13.2 | — |
| `telegramAiSummaries` | Boolean | `true` | Показывать AI-сводки Telegram |  | `TranslateController.java` | ❓ | проверить наличие в TG-iOS | — |
| `telegramAiInstantViewSummaries` | Boolean | `true` | AI-сводки в Instant View |  | `ArticleViewer.java` | ❓ | проверить наличие в TG-iOS | — |
| `quickAdminShortcuts` | Boolean | `true` | Быстрые админ-действия | Чаты / Chats → «Quick Admin Shortcuts» | `ChatActivity.java` | ⚠️ |  | — |
| `quickTransitionForChannels` | Boolean | `` | Переход к следующему каналу свайпом |  | `ChatActivity.java` | ✅ |  | SG:disableScrollToNextChannel (совпадает) |
| `quickTransitionForTopics` | Boolean | `true` | Переход к следующему топику свайпом |  | `ChatActivity.java` | ✅ |  | SG:disableScrollToNextTopic (совпадает) |
| `disableGreetingSticker` | Boolean | `false` | Отключить приветственный стикер в пустом чате | Чаты / Chats → «Disable Greeting Sticker» | `ChatGreetingsView.java` | ✅ |  | — |
| `autoRunWidgets` | Boolean | `false` | Автоматически запускать виджеты в сообщениях | Чаты / Chats → «Run Widgets Automatically» | `WidgetMedia.java` | ❓ | уточнить, что такое «виджеты» в 13.x (в TG-iOS есть message widgets — docs/message-widgets-native-runtime.md) | TG? |
| `hideKeyboardOnScroll` | Boolean | `true` | Скрывать клавиатуру при прокрутке | Чаты / Chats → «Hide Keyboard on Scroll» | `ChatActivity.java` | ✅ |  | — (в TG-iOS interactive dismiss) |
| `addCommaAfterMention` | Boolean | `true` | Запятая после упоминания | Чаты / Chats → «Add Comma after Mention» | `ChatActivity.java`, `MentionsContainerView.java` | ✅ |  | — |
| `inlineResults` | Boolean | `true` | Инлайн-результаты в поле ввода (общий переключатель) |  | exteragram: `InlineResults.kt` | ✅ | чистая логика + UI-подсказка над полем ввода | — |
| `inlineMathResult` | Boolean | `true` | Калькулятор в поле ввода | Чаты / Sticker Shape → «Inline Results» | exteragram: `InlineResults.kt` | ✅ |  | — |
| `inlineCurrencyRates` | Boolean | `true` | Курсы валют | Чаты → Инлайн-результаты / Features → «Currencies» | exteragram: `InlineResults.kt` | ⚠️ | внешний сервис open.er-api.com — вопрос | — |
| `inlineUnitConversion` | Boolean | `true` | Перевод единиц измерения | Чаты → Инлайн-результаты / Features → «Units of Measure» | exteragram: `InlineResults.kt` | ✅ |  | — |
| `inlineTimeZones` | Boolean | `false` | Часовые пояса | Чаты → Инлайн-результаты / Features → «Time Zones» | exteragram: `InlineMathController.kt`, `InlineResults.kt` | ✅ |  | — |
| `inlineTargetCurrency` | String | `""` | Валюта по умолчанию | Чаты → Инлайн-результаты / Settings → «Default Currency» | exteragram: `InlineRates.kt` | ✅ |  | — |
| `inlineAngleUnit` | Enum | `AngleUnit.DEGREES` | Градусы / радианы для sin, cos, tan | Чаты → Инлайн-результаты / Settings → «Angles in sin, cos, tan» | exteragram: `InlineResults.kt` | ✅ |  | — |
| `inlineMeasureSystem` | Enum | `MeasureSystem.AUTO` | Система мер: авто / метрическая / имперская | Чаты → Инлайн-результаты / Settings → «Measurement System» | exteragram: `InlineResults.kt` | ✅ |  | — |
| `inlineDigitGrouping` | Boolean | `true` | Группировка разрядов | Чаты → Инлайн-результаты / Settings → «Group Digits» | exteragram: `InlineResults.kt` | ✅ |  | — |
| `disableMarkdown` | Boolean | `false` | Отключить Markdown при отправке |  | `MediaDataController.java`, `EditTextBoldCursor.java` | ✅ |  | — |
| `hideSendAsPeer` | Boolean | `false` | Скрыть кнопку «Отправить от имени» | Чаты / Chats → «Hide \"Send as…\" Button» | `ChatActivityEnterView.java` | ✅ |  | SG:disableSendAsButton (совпадает) |
| `removeMessageTail` | Boolean | `true` | Убрать «хвостик» у пузыря сообщения | Чаты / Messages → «Remove Message Tail» | `MessageDrawable.java`, `ChatMessageCell.java` | ⚠️ | отрисовка пузырей в TG-iOS (PresentationThemeBubble) | — |
| `replaceEditedWithIcon` | Boolean | `true` | Иконка вместо слова «изменено» | Чаты / Messages → «Replace \"%1$s\" with an Icon» | `ChatMessageCell.java` | ⚠️ | ChatMessageDateAndStatusNode | — |
| `showOnlineStatus` | Boolean | `false` | Индикатор онлайна у аватарок в чатах | Чаты / Messages → «Show Online Indicator» | `ChatMessageCell.java` | ⚠️ |  | — |
| `showForwardsCount` | Boolean | `false` | Показывать число пересылок | Чаты / Messages → «Show Forward Count» | exteragram: `ChatMessageCellUiHelper.java` | ✅ |  | — |
| `hideShareButton` | Boolean | `true` | Скрыть боковую кнопку «Поделиться» | Чаты / Messages → «Hide Side \"%1$s\" Button» | `ChatMessageCell.java` | ✅ |  | — |
| `showResultsBeforeVoting` | Boolean | `false` | Результаты опроса до голосования | Чаты / Messages → «Show Results Before Voting» | `MessagesController.java`, `ChatMessagePoll.java` | ❓ | уточнить, как exteraGram получает результаты | — |
| `showCopyPhotoButton` | Boolean | `true` | Меню сообщения: «Копировать фото» |  | `ChatActivity.java` | ✅ |  | TG (есть копирование) / SG:contextShow* |
| `showSaveMessageButton` | Boolean | `false` | Меню сообщения: «Сохранить в Избранное» |  | `ChatActivity.java` | ✅ |  | SG:contextShowSaveToCloud (совпадает) |
| `showRepeatMessageButton` | Boolean | `false` | Меню сообщения: «Повторить» |  | `ChatActivity.java` | ✅ |  | — |
| `showClearButton` | Boolean | `true` | Меню сообщения: «Очистить» |  | `ChatActivity.java` | ❓ | уточнить действие | — |
| `showHistoryButton` | Boolean | `false` | Меню сообщения: «История» |  | `ChatActivity.java` | ❓ | уточнить действие | — |
| `showReportButton` | Boolean | `true` | Меню сообщения: «Пожаловаться» |  | `ChatActivity.java` | ✅ |  | SG:contextShowReport (совпадает) |
| `showGenerateButton` | Boolean | `true` | Меню сообщения: «Сгенерировать» (AI) |  | `ChatActivity.java` | ⚠️ | зависит от модуля ai | — |
| `showDetailsButton` | Boolean | `false` | Меню сообщения: «Подробнее» (JSON/детали) |  | `ChatActivity.java` | ✅ |  | SG:contextShowJson (частично) |
| `groupMessageMenu` | Boolean | `true` | Группировать пункты меню сообщения | Чаты / Messages → «Group Message Menu» | `ActionBarPopupWindow.java`, `ChatActivity.java` | ⚠️ | ContextMenu TG-iOS | — |
| `recognitionLanguage` | String | `"none"` | Язык офлайн-распознавания речи (Vosk) | Чаты / Voice-to-Text Conversion → «Recognition Language» | `TranscribeButton.java`; exteragram: `VoiceRecognitionController.java` | ⚠️ | Vosk для iOS или SFSpeechRecognizer on-device — вопрос C20 | SG:transcriptionBackend (apple) (частично) |
| `postprocessingWithAi` | Boolean | `false` | AI-постобработка распознанного текста | Чаты / Voice-to-Text Conversion → «Use AI for post-processing» | exteragram: `VoiceRecognitionController.java` | ⚠️ | зависит от модуля ai | — |
| `cameraType` | Enum | `if (SharedConfig.getDevicePerformanceCla` | Тип камеры: Camera1 / Camera2 / CameraX | Чаты / Camera → «Camera Type» | `InstantCameraView.java`, `InstantCameraViewBase.java`; exteragram: `RoundVideoUiHelper.java` | ❌ | Android API; на iOS только AVFoundation | — |
| `extendedFramesPerSecond` | Boolean | `false` | Камера: повышенная частота кадров |  | `Camera2Session.java`, `InstantCameraView.java`; exteragram: `CameraXSession.java`, `RoundVideoUiHelper.java` | ⚠️ | AVCaptureDevice.activeFormat | — |
| `cameraStabilization` | Boolean | `false` | Камера: стабилизация |  | `Camera2Session.java`; exteragram: `CameraXSession.java`, `RoundVideoCamera2Helper.java` +1 | ⚠️ | AVCaptureConnection.preferredVideoStabilizationMode | — |
| `cameraMirrorMode` | Boolean | `true` | Камера: зеркалирование фронтальной |  | exteragram: `CameraXSession.java` | ⚠️ |  | — |
| `videoMessagesCamera` | Enum | `` | Камера для видеокружков: фронтальная / тыловая / спрашивать | Чаты / Camera → «Camera in Video Messages» | `ChatActivityEnterView.java`, `InstantCameraView.java`; exteragram: `RoundVideoUiHelper.java` | ✅ |  | SG:startTelescopeWithRearCam (частично) |
| `rememberLastUsedCamera` | Boolean | `false` | Запоминать последнюю камеру | Чаты / Camera → «Remember Last Used Camera» | `InstantCameraView.java`; exteragram: `RoundVideoUiHelper.java` | ✅ |  | — |
| `startWithWideAngleCamera` | Boolean | `false` | Начинать со сверхширокой камеры |  | exteragram: `CameraXSession.java`, `InstantCameraZoomSlider.java` +1 | ⚠️ | выбор AVCaptureDevice | — |
| `zoomSlider` | Boolean | `true` | Слайдер зума в камере кружков | Чаты / Camera → «Zoom Slider» | `ChatActivity.java`, `InstantCameraView.java`, `InstantCameraViewBase.java`; exteragram: `InstantCameraZoomSlider.java`, `RoundVideoUiHelper.java` | ⚠️ | UI камеры TG-iOS | — |
| `staticZoom` | Boolean | `false` | Фиксированный зум | Чаты / Camera → «Static Zoom» | `InstantCameraView.java`; exteragram: `InstantCameraZoomSlider.java` | ⚠️ |  | — |
| `alwaysSendInHD` | Boolean | `true` | Всегда отправлять фото в HD | Чаты / Photos → «Always Send in HD» | `MediaController.java`, `PhotoAttachPhotoCell.java` | ✅ |  | SG:sendLargePhotos / SG:outgoingPhotoQuality (совпадает) |
| `hideCameraTile` | Boolean | `false` | Скрыть плитку камеры в галерее | Чаты / Photos → «Hide Instant Camera Tile» | `ChatAttachAlert.java`, `ChatAttachAlertPhotoLayout.java` | ✅ |  | SG:disableGalleryCamera (совпадает) |
| `doubleTapSeekDuration` | Integer | `1` | Перемотка видео двойным тапом: 5/10/15/30 с | Чаты / Videos → «Double Tap Skip Time» | `PhotoViewer.java` | ✅ |  | — |
| `preferOriginalQuality` | Boolean | `false` | Предпочитать оригинальное качество видео | Чаты / Videos → «Prefer Original Quality» | `VideoPlayer.java` | ✅ |  | — |
| `swipeToPip` | Boolean | `false` | Свайп для картинки-в-картинке | Чаты / Videos → «Swipe to PiP» | `PhotoViewer.java` | ✅ |  | SG:videoPIPSwipeDirection (совпадает) |
| `unmuteWithVolumeButtons` | Boolean | `false` | Включать звук видео кнопками громкости | Чаты / Videos → «Unmute Videos with Volume Buttons» | `LaunchActivity.java` | ⚠️ | на iOS — наблюдение за AVAudioSession.outputVolume | — |
| `pauseOnMinimizeVideo` | Boolean | `true` | Пауза видео при сворачивании |  | `PhotoViewer.java` | ⚠️ |  | — |
| `pauseOnMinimizeVoice` | Boolean | `false` | Пауза голосового при сворачивании |  | `MediaController.java` | ⚠️ |  | — |
| `pauseOnMinimizeRound` | Boolean | `false` | Пауза кружка при сворачивании |  | `MediaController.java` | ⚠️ |  | — |
| `messageExportWatermark` | Boolean | `true` | Экспорт сообщения картинкой: водяной знак |  | exteragram: `MessageExportWatermark.java`, `MessageExportSheet.java` | ⚠️ | пакет messageexport — 7,2 тыс. строк; водяной знак exteraGram — см. п. D22 | — |
| `messageExportSource` | Boolean | `true` | Экспорт сообщения картинкой: источник |  | exteragram: `MessageExportChatContext.java`, `MessageExportSheet.java` | ⚠️ | часть messageexport | — |
| `messageExportAuthors` | Boolean | `false` | Экспорт сообщения картинкой: авторы |  | exteragram: `MessageExportChatContext.java`, `MessageExportSheet.java` | ⚠️ | часть messageexport | — |
| `messageExportTime` | Boolean | `true` | Экспорт сообщения картинкой: время |  | exteragram: `MessageExportChatContext.java`, `MessageExportSheet.java` | ⚠️ | часть messageexport | — |

### Other

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `useGoogleCrashlytics` | Boolean | `BuildVars.isBetaApp(` | Отправлять отчёты о сбоях в Firebase Crashlytics | Другое → «crashlytics» | `ApplicationLoader.java` | ❌ | без своего Firebase-проекта — вопрос C15 | — |
| `useGoogleAnalytics` | Boolean | `false` | Firebase Analytics | Другое → «analytics» | `ApplicationLoader.java` | ❌ | вопрос C15 | — |
| `enableAdBlock` | Boolean | `true` | Блокировщик рекламы (спонсорские сообщения, фильтры uBlock/AdGuard) |  | exteragram: `AdBlockManager.java`, `AdBlockMenuItem.java` | ⚠️ | нативная часть (JNI) собрана под Android — переписать или собрать под iOS; списки фильтров внешние | — |

### Data export

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `exportTypes` | Integer | `ExportSettings.DefaultTypes` | Экспорт данных: типы |  | exteragram: `ExportActivity.kt` | ⚠️ | пакет export — 13 тыс. строк, на iOS новый экран | — |
| `exportFullChats` | Integer | `ExportSettings.DefaultFullChats` | Экспорт данных: чаты целиком |  | exteragram: `ExportActivity.kt` | ⚠️ | часть export | — |
| `exportMediaTypes` | Integer | `ExportSettings.MediaSettings.Photo` | Экспорт данных: типы медиа |  | exteragram: `ExportActivity.kt` | ⚠️ | часть export | — |
| `exportSizeLimit` | Long | `8L * 1024 * 1024` | Экспорт данных: лимит размера файла |  | exteragram: `ExportActivity.kt` | ⚠️ | часть export | — |
| `exportFormat` | Enum | `ExportSettings.Format.Html` | Экспорт данных: HTML / JSON |  | exteragram: `ExportActivity.kt` | ⚠️ | часть export | — |
| `exportFolder` | String | `""` | Экспорт данных: папка |  | exteragram: `ExportActivity.kt` | ⚠️ | на iOS — выбор папки в «Файлах» | — |

### Updates

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `updateScheduleTimestamp` | Long | `0L` | Отложенная проверка обновлений APK |  | `LaunchActivity.java`; exteragram: `UpdateAppAlertDialog.java` | ❌ | Android-апдейтер; при sideload — ссылка на GitHub Releases | — |
| `sdkUpdateScheduleTimestamp` | Long | `0L` | Отложенная проверка обновлений SDK плагинов |  | exteragram: `PythonPluginsEngine.kt` | ⚠️ | OTA SDK — вопрос C18 | — |

### Misc

| Ключ | Тип | По умолчанию | Что делает | Где в интерфейсе | Android: где используется | iOS | Как / почему | Аналог |
|---|---|---|---|---|---|---|---|---|
| `targetLang` | String | `TranslatorUtils.TARGET_LANG_FOLLOW_APP` | Целевой язык перевода |  | exteragram: `TranslatorUtils.java` | ✅ |  | SG:outgoingLanguageTranslation (другое) / TG |
| `flashWarmth` | Float | `0.5f` | Фронтальная вспышка: теплота |  | exteragram: `RoundVideoUiHelper.java` | ⚠️ | в TG-iOS есть фронтальная вспышка для кружков, проверить | — |
| `flashIntensity` | Float | `1f` | Фронтальная вспышка: яркость |  | exteragram: `RoundVideoUiHelper.java` | ⚠️ | то же | — |
| `pluginsEngine` | runtime | `false` | Движок плагинов включён |  | `ApplicationLoader.java`; exteragram: `PluginsController.kt`, `PythonPluginsEngine.kt` +5 | ⚠️ | этап 5 | — |
| `pluginsDevMode` | Boolean | `false` | Режим разработчика плагинов (dev server) |  | exteragram: `PythonPluginsEngine.kt`, `PluginsInfoActivity.kt` | ⚠️ | этап 5 | — |
| `pluginsSafeMode` | Boolean | `false` | Безопасный режим плагинов |  | exteragram: `PluginsController.kt`, `PythonPluginsEngine.kt` +5 | ⚠️ | этап 5 | — |
| `pluginsCompactView` | Boolean | `false` | Компактный список плагинов |  | exteragram: `PluginsInfoActivity.kt`, `PluginCell.kt` | ✅ | этап 5 | — |
| `pluginsPySdkAutoUpdate` | Boolean | `false` | Автообновление Python SDK |  | exteragram: `PythonPluginsEngine.kt`, `AnalyzerUpdater.kt` +1 | ⚠️ | только со своим ключом — C18 | — |
| `pluginsPySdkBetaVersions` | Boolean | `false` | Бета-версии SDK |  | exteragram: `PythonPluginsEngine.kt`, `AnalyzerUpdater.kt` +1 | ⚠️ | C18 | — |
| `pluginsDisableArtOpts` | Boolean | `false` | Отключить оптимизации ART для хуков |  | exteragram: `PluginsController.kt`, `PluginsInfoActivity.kt` | ❌ | ART есть только на Android | — |
| `pluginsUnknownSources` | Boolean | `false` | Разрешить плагины из неизвестных источников |  | exteragram: `PluginsInfoActivity.kt`, `InstallPluginBottomSheet.kt` | ✅ | этап 5 | — |
| `pluginsStaticAnalysis` | Boolean | `true` | Статический анализ плагинов перед установкой |  | exteragram: `AnalyzerUpdater.kt`, `PluginsInfoActivity.kt` +1 | ⚠️ | анализатор — закрытый .so под Android, вопрос C19 | — |
| `pinnedPlugins` | StringSet | `emptySet(` | Закреплённые плагины |  | exteragram: `PluginsController.kt`, `PluginsActivity.kt` | ✅ | этап 5 | — |
| `useSystemIconShape` | Boolean | `true` | Форма иконок по системной теме |  | exteragram: `AppIconPreviewView.java` | ❌ | адаптивные иконки Android | — |

## 2. Пункты настроек без ключа в `ExteraConfig`

Эти пункты хранят значения в настройках самого Telegram или открывают отдельные экраны.

| linkAlias | Где | Тип пункта |
|---|---|---|
| `showTranslateButton` | Основные / Translate Messages → «Show Translate Button» | uCheck |
| `showTranslateChatButton` | Основные / Translate Messages → «Translate Entire Chat» | uCheck |
| `translationTargetLanguage` | Основные / Translate Messages → «Target Language» | uButton |
| `doNotTranslateLanguages` | Основные / Translate Messages → «Do Not Translate» | uButton |
| `general` | Главный экран / Categories → «General» | uButton |
| `appearance` | Главный экран / Categories → «Appearance» | uButton |
| `chats` | Главный экран / Categories → «Chats» | uButton |
| `plugins` | Главный экран / Categories → «Plugins» | uButton |
| `other` | Главный экран / Categories → «Other» | uButton |
| `crowdin` | Главный экран / Links → «Translate» | uButton |
| `sourceCode` | Главный экран / Links → «Source Code» | uButton |
| `exportData` | Другое → «Export Data» | uButton |
| `exportSettings` | Другое → «Export Settings» | uButton |
| `resetSettings` | Другое → «Reset Settings» | uButton |
| `deleteAccount` | Другое → «Delete Account» | uButton |
| `bottomNavigationBarMode` | Оформление → Навигация / General → «Bottom Navigation Bar» | uButton |
| `appNavigationSettings` | Оформление / Folders → «App Navigation» | uButton |
| `appIcon` | Оформление / Folders → «App Icon» | uButton |
| `iconPacks` | Оформление / Folders → «Icon Packs» | uButton |
| `pillStack` | Оформление / Folders → «Pill Stack» | uButton |
| `useSystemEmoji` | Оформление / Appearance → «Use System Emoji» | uCheck |
| `aiChat` | Чаты / Sticker Shape → «AI Chat» | uButton |
| `chatSettings` | Чаты / Sticker Shape → «Chat Settings» | uButton |
| `deleteRecognitionModel` | Чаты / Voice-to-Text Conversion → «Delete Model» | uButton |

## 3. Пакеты функций `com/exteragram/messenger/`

| Пакет | Что делает | iOS | Комментарий |
|---|---|---|---|
| `adblock` | Блокировка рекламы и спонсорских сообщений, фильтры uBlock/AdGuard, нативная часть через JNI | ⚠️ | нативную часть пересобрать под iOS или переписать; списки фильтров внешние (filters.adtidy.org, ublockorigin.github.io) |
| `ai` | AI-функции: чат, генерация, постобработка; провайдеры Gemini, OpenAI, OpenRouter, Perplexity (ключи вводит пользователь) | ⚠️ | HTTP-клиенты переносятся; UI новый |
| `api` | Клиент сервера exteraGram `api.exteragram.app/api/v1` (профили, now-playing, boosty) | ⚠️ | вопрос C14 — разрешение на использование сервера |
| `appicons` | Альтернативные иконки приложения | ⚠️ | на iOS — `setAlternateIconName`; иконки и бренд — вопрос D22 |
| `backup` | Экспорт, импорт и сброс настроек exteraGram | ✅ | формат файла можно сделать совместимым |
| `badges` | Значки сапортеров и донатов (с сервера exteraGram) | ⚠️ | зависит от C14 |
| `camera` | Своя камера (CameraX), кружки, вспышка | ⚠️ | только настройки поверх камеры Telegram-iOS (AVFoundation); саму камеру не переносим |
| `components` | Общие UI-компоненты | ⚠️ | переносятся по месту использования |
| `debug` | Отладочные экраны и мониторы (зависания, heap, нагрузка) | ⚠️ | частично есть в SGDebugUI |
| `drawer` | Боковое меню и редактор его пунктов | ⚠️ | на iOS нетипично — спросить |
| `export` | Экспорт данных чатов (HTML/JSON), как в Telegram Desktop | ⚠️ | новый экран; файлы в «Файлы» через UIDocumentPicker |
| `feed` | Лента постов каналов с категориями | ⚠️ | новый экран поверх Postbox |
| `icons` | Наборы иконок интерфейса (Solar, Remix) и их редактор | ⚠️ | нужны ассеты под iOS |
| `inline` | Калькулятор, валюты, единицы и часовые пояса прямо в поле ввода | ✅ | логика переносится; курсы — внешний сервис open.er-api.com |
| `messageexport` | Экспорт сообщения картинкой | ⚠️ | рендер через UIGraphicsImageRenderer |
| `notifications` | Уведомления по аккаунтам, аватарки в уведомлениях | ⚠️ | на iOS — Notification Service Extension; без пушей (бесплатный Apple ID) — ограниченно |
| `nowplaying` | «Сейчас играет» в профиле (Spotify, Last.fm, stats.fm и др.) | ⚠️ | зависит от C14 и внешних сервисов |
| `pdf` | Встроенный просмотрщик PDF с выделением текста | ✅ | на iOS — PDFKit |
| `pillstack` | Интерактивные «пилюли» в поле поиска (курсы, погода и т. п.), шаблоны, импорт, пилюли из плагинов | ⚠️ | новый UI; сетевые шаблоны |
| `player` | Новый музыкальный плеер: обложки, тексты, canvas, ритм | ⚠️ | самый большой модуль (18,9 тыс. строк), писать заново |
| `preferences` | Экраны настроек exteraGram | ⚠️ | на iOS — ItemListUI, как SGSettingsUI |
| `profilecolor` | Цвета и темы профиля, отладочный экран палитры | ❓ | уточнить, что из этого пользовательская функция |
| `proxy` | Информация об IP прокси, условия отключения прокси | ⚠️ | см. doNotUseProxy |
| `reactions` | Редактор быстрых реакций | ⚠️ |  |
| `regdate` | Примерная дата регистрации аккаунта | ✅ | аналог: SGRegDate (совпадает, сравнить источники) |
| `security` | Подтверждение чувствительных запросов (платёжные формы и т. п.) | ⚠️ | перехват запросов в TelegramCore |
| `speech` | Офлайн-распознавание речи (Vosk, модели с alphacephei.com) | ⚠️ | вопрос C20; альтернатива — SFSpeechRecognizer |
| `translator` | Перевод: Google, Microsoft, Yandex, Telegram | ⚠️ | аналог: SGTranslate/SGGTranslate — расширить |
| `updater` | Обновление APK | ❌ | Android-only; при sideload — уведомление о новой версии на GitHub |
| `utils` | Утилиты | ⚠️ | по месту |

Плагины (версия `full`) разобраны отдельно в `PLUGINS_ANDROID.md`.

## 4. Что на iOS бессмысленно или невозможно и чем заменить

| Что | Почему | Предложение |
|---|---|---|
| Material You / Monet, адаптивные иконки (`useSystemIconShape`) | нет в iOS | не переносить; цвета берём из тем Telegram-iOS |
| Android-контролы (`newSwitchStyle`, `newSliderStyle`, `newLoadingStyle`), FAB (`squareFab`, `newFabStyle`, `hideFloatingButton`) | на iOS системные контролы, FAB нет | не переносить |
| `transitionAnimation`, `predictiveBackIntensity` | анимации и жесты Android | не переносить; на iOS системный push и свайп назад |
| `cameraType` (Camera1/2/X) | Android API | не переносить; остальные настройки камеры — через AVFoundation |
| `useSystemFonts`, `centerTitle` | на iOS и так системный шрифт и заголовок по центру | не переносить |
| Апдейтер APK (`updater`, `updateScheduleTimestamp`) | установка APK | проверка новой версии на GitHub Releases и ссылка для Sideloadly |
| Версии `lite` / `full` | разделение сборок Android | одна сборка; плагины включаются переключателем |
| Android-интенты и файловые хуки плагинов | нет аналога интентов | URL-схема и Share Extension — этап 5 |
| `customSavePath` | нет общей файловой системы | «Сохранить в Файлы» |
| `pluginsDisableArtOpts`, ART-хуки | ART есть только на Android | именованные точки расширения в Swift — этап 5 |
| Firebase (Crashlytics, Analytics, Messaging, Remote Config) | чужой проект использовать нельзя | вопрос C15 |

## 5. Внешние сервисы, найденные в коде (вопросы о разрешении — этап 2)

`api.exteragram.app`, `plugins.exteragram.app`, `alphacephei.com` (модели Vosk), `filters.adtidy.org` и `ublockorigin.github.io` (фильтры рекламы), `generativelanguage.googleapis.com`, `api.perplexity.ai`, `openrouter.ai` (AI с ключом пользователя), `lrclib.net` и `lyrics-api.boidu.dev` (тексты), `spclient.wg.spotify.com`, `open.spotify.com`, `accounts.spotify.com`, `music.apple.com`, Yandex Music, `music.163.com`, `y.qq.com`, `last.fm`, `stats.fm`, `pipe.deezer.com` (now-playing, canvas, обложки), `open.er-api.com` (курсы валют), `translate.yandex.net`, `toncenter.com`, `dns.comss.one` (DoH).

## 6. Что нужно уточнить (❓)

- `disableNotificationDelay` — Отключить задержку уведомлений: на Android это задержка показа, когда приложение открыто. На iOS уведомления устроены иначе, нужно сравнить с кодом Telegram-iOS
- `newChatHeaderStyle` — Новый стиль шапки чата: нужно разобрать, что меняется визуально
- `playerMode` — Режим плеера: уточнить значения
- `customThemes` — Темы чатов (custom themes) в чатах: уточнить, что именно отключается
- `stickerShape` — Форма стикеров (секция «Форма стикера»): уточнить варианты
- `telegramAiEditor` — Показывать AI-редактор Telegram: проверить, есть ли эта функция в Telegram-iOS 13.2
- `telegramAiSummaries` — Показывать AI-сводки Telegram: проверить наличие в TG-iOS
- `telegramAiInstantViewSummaries` — AI-сводки в Instant View: проверить наличие в TG-iOS
- `autoRunWidgets` — Автоматически запускать виджеты в сообщениях: уточнить, что такое «виджеты» в 13.x (в TG-iOS есть message widgets — docs/message-widgets-native-runtime.md)
- `showResultsBeforeVoting` — Результаты опроса до голосования: уточнить, как exteraGram получает результаты
- `showClearButton` — Меню сообщения: «Очистить»: уточнить действие
- `showHistoryButton` — Меню сообщения: «История»: уточнить действие

## 7. Файлы `org.telegram.*` с изменениями exteraGram (325)

| Пакет | Файлов |
|---|---|
| `org.telegram.ui.Components` | 94 |
| `org.telegram.ui` | 66 |
| `org.telegram.ui.Cells` | 42 |
| `org.telegram.messenger` | 29 |
| `org.telegram.ui.ActionBar` | 15 |
| `org.telegram.ui.Stories.recorder` | 7 |
| `org.telegram.ui.Stories` | 6 |
| `org.telegram.ui.Adapters` | 4 |
| `org.telegram.ui.Components.Premium` | 4 |
| `org.telegram.ui.Components.Reactions` | 4 |
| `org.telegram.ui.web` | 4 |
| `org.telegram.messenger.video` | 3 |
| `org.telegram.ui.Gifts` | 3 |
| `org.telegram.ui.QrShare` | 3 |
| `org.telegram.ui.Stars` | 3 |
| `org.telegram.ui.community` | 3 |
| `org.telegram.ui.iv` | 3 |
| `org.telegram.ui.Components.Paint.Views` | 2 |
| `org.telegram.ui.Components.blur3` | 2 |
| `org.telegram.ui.Components.quickforward` | 2 |
| `org.telegram.ui.bots` | 2 |
| `org.telegram.ui.community.cells` | 2 |
| `org.telegram.utils.recorder.round` | 2 |
| `org.telegram.messenger.audioinfo` | 1 |
| `org.telegram.messenger.audioinfo.m4a` | 1 |
| `org.telegram.messenger.audioinfo.mp3` | 1 |
| `org.telegram.messenger.camera` | 1 |
| `org.telegram.messenger.voip` | 1 |
| `org.telegram.tgnet` | 1 |
| `org.telegram.ui.Business` | 1 |
| `org.telegram.ui.Charts` | 1 |
| `org.telegram.ui.Components.Crop` | 1 |
| `org.telegram.ui.Components.Premium.GLIcon` | 1 |
| `org.telegram.ui.Components.Premium.boosts.cells.selector` | 1 |
| `org.telegram.ui.Components.blur3.drawable` | 1 |
| `org.telegram.ui.Components.blur3.drawable.color.impl` | 1 |
| `org.telegram.ui.Components.chat.buttons` | 1 |
| `org.telegram.ui.Components.glass` | 1 |
| `org.telegram.ui.Delegates` | 1 |
| `org.telegram.ui.TON` | 1 |
| `org.telegram.utils.glass` | 1 |
| `org.telegram.utils.glass.fade` | 1 |
| `org.telegram.utils.twidget` | 1 |

<details><summary>Полный список</summary>

- `org/telegram/messenger/AndroidUtilities.java`
- `org/telegram/messenger/ApplicationLoader.java`
- `org/telegram/messenger/BotWebViewVibrationEffect.java`
- `org/telegram/messenger/BuildVars.java`
- `org/telegram/messenger/ChatThemeController.java`
- `org/telegram/messenger/ChatsWidgetService.java`
- `org/telegram/messenger/ContactsWidgetService.java`
- `org/telegram/messenger/Emoji.java`
- `org/telegram/messenger/FileLoadOperation.java`
- `org/telegram/messenger/FileRefController.java`
- `org/telegram/messenger/FileUploadOperation.java`
- `org/telegram/messenger/FilesMigrationService.java`
- `org/telegram/messenger/FingerprintController.java`
- `org/telegram/messenger/HashtagSearchController.java`
- `org/telegram/messenger/ImageLoader.java`
- `org/telegram/messenger/LocaleController.java`
- `org/telegram/messenger/MediaController.java`
- `org/telegram/messenger/MediaDataController.java`
- `org/telegram/messenger/MessageObject.java`
- `org/telegram/messenger/MessagesController.java`
- `org/telegram/messenger/MessagesStorage.java`
- `org/telegram/messenger/MusicPlayerService.java`
- `org/telegram/messenger/NotificationsController.java`
- `org/telegram/messenger/PasskeysController.java`
- `org/telegram/messenger/ProxyRotationController.java`
- `org/telegram/messenger/RichMessageLayout.java`
- `org/telegram/messenger/SendMessagesHelper.java`
- `org/telegram/messenger/SharedConfig.java`
- `org/telegram/messenger/TranslateController.java`
- `org/telegram/messenger/audioinfo/OtherAudioInfo.java`
- `org/telegram/messenger/audioinfo/m4a/M4AInfo.java`
- `org/telegram/messenger/audioinfo/mp3/ID3v2Info.java`
- `org/telegram/messenger/camera/Camera2Session.java`
- `org/telegram/messenger/video/TextureRenderer.java`
- `org/telegram/messenger/video/VideoAds.java`
- `org/telegram/messenger/video/WebmEncoder.java`
- `org/telegram/messenger/voip/VoIPService.java`
- `org/telegram/tgnet/ConnectionsManager.java`
- `org/telegram/ui/ActionBar/ActionBar.java`
- `org/telegram/ui/ActionBar/ActionBarLayout.java`
- `org/telegram/ui/ActionBar/ActionBarMenuItem.java`
- `org/telegram/ui/ActionBar/ActionBarMenuSlider.java`
- `org/telegram/ui/ActionBar/ActionBarMenuSubItem.java`
- `org/telegram/ui/ActionBar/ActionBarPopupWindow.java`
- `org/telegram/ui/ActionBar/AlertDialog.java`
- `org/telegram/ui/ActionBar/BaseFragment.java`
- `org/telegram/ui/ActionBar/BottomSheet.java`
- `org/telegram/ui/ActionBar/DrawerLayoutContainer.java`
- `org/telegram/ui/ActionBar/MessageDrawable.java`
- `org/telegram/ui/ActionBar/MonetAccentHelper.java`
- `org/telegram/ui/ActionBar/SimpleActionBar.java`
- `org/telegram/ui/ActionBar/SimpleTextView.java`
- `org/telegram/ui/ActionBar/Theme.java`
- `org/telegram/ui/Adapters/DialogsAdapter.java`
- `org/telegram/ui/Adapters/DialogsSearchAdapter.java`
- `org/telegram/ui/Adapters/FiltersView.java`
- `org/telegram/ui/Adapters/MentionsAdapter.java`
- `org/telegram/ui/ArticleViewer.java`
- `org/telegram/ui/AvatarSpan.java`
- `org/telegram/ui/Business/BusinessBotButton.java`
- `org/telegram/ui/CacheControlActivity.java`
- `org/telegram/ui/CachedMediaLayout.java`
- `org/telegram/ui/CalendarActivity.java`
- `org/telegram/ui/CallLogActivity.java`
- `org/telegram/ui/Cells/AccountSelectCell.java`
- `org/telegram/ui/Cells/AdminedChannelCell.java`
- `org/telegram/ui/Cells/ChannelRecommendationsCell.java`
- `org/telegram/ui/Cells/ChatActionCell.java`
- `org/telegram/ui/Cells/ChatMessageCell.java`
- `org/telegram/ui/Cells/ChatMessagePoll.java`
- `org/telegram/ui/Cells/CheckBoxCell.java`
- `org/telegram/ui/Cells/CheckBoxUserCell.java`
- `org/telegram/ui/Cells/DialogCell.java`
- `org/telegram/ui/Cells/DialogMeUrlCell.java`
- `org/telegram/ui/Cells/DialogsEmptyCell.java`
- `org/telegram/ui/Cells/DialogsHintCell.java`
- `org/telegram/ui/Cells/DividerCell.java`
- `org/telegram/ui/Cells/GroupCallInvitedCell.java`
- `org/telegram/ui/Cells/GroupCallUserCell.java`
- `org/telegram/ui/Cells/GroupCreateUserCell.java`
- `org/telegram/ui/Cells/HeaderCell.java`
- `org/telegram/ui/Cells/HintDialogCell.java`
- `org/telegram/ui/Cells/InviteUserCell.java`
- `org/telegram/ui/Cells/JoinSheetUserCell.java`
- `org/telegram/ui/Cells/ManageChatUserCell.java`
- `org/telegram/ui/Cells/MemberRequestCell.java`
- `org/telegram/ui/Cells/MentionCell.java`
- `org/telegram/ui/Cells/PhotoAttachPhotoCell.java`
- `org/telegram/ui/Cells/ProfileSearchCell.java`
- `org/telegram/ui/Cells/ReactedUserHolderView.java`
- `org/telegram/ui/Cells/SessionCell.java`
- `org/telegram/ui/Cells/ShareDialogCell.java`
- `org/telegram/ui/Cells/SharedDocumentCell.java`
- `org/telegram/ui/Cells/SharedLinkCell.java`
- `org/telegram/ui/Cells/SharingLiveLocationCell.java`
- `org/telegram/ui/Cells/SlideIntChooseView.java`
- `org/telegram/ui/Cells/StickerCell.java`
- `org/telegram/ui/Cells/StickerEmojiCell.java`
- `org/telegram/ui/Cells/TextCheckCell.java`
- `org/telegram/ui/Cells/TextCheckCell2.java`
- `org/telegram/ui/Cells/TextDetailCell.java`
- `org/telegram/ui/Cells/TextSelectionHelper.java`
- `org/telegram/ui/Cells/ThemePreviewMessagesCell.java`
- `org/telegram/ui/Cells/UserCell.java`
- `org/telegram/ui/Cells/UserCell2.java`
- `org/telegram/ui/Cells/UserInfoCell.java`
- `org/telegram/ui/ChangeUsernameActivity.java`
- `org/telegram/ui/ChannelAdminLogActivity.java`
- `org/telegram/ui/ChannelCreateActivity.java`
- `org/telegram/ui/ChannelMonetizationLayout.java`
- `org/telegram/ui/Charts/BaseChartView.java`
- `org/telegram/ui/ChatActivity.java`
- `org/telegram/ui/ChatEditActivity.java`
- `org/telegram/ui/ChatLinkActivity.java`
- `org/telegram/ui/ChatPullingDownDrawable.java`
- `org/telegram/ui/Components/AIEditorAlert.java`
- `org/telegram/ui/Components/AlertsCreator.java`
- `org/telegram/ui/Components/AudioPlayerAlert.java`
- `org/telegram/ui/Components/AvatarConstructorFragment.java`
- `org/telegram/ui/Components/AvatarDrawable.java`
- `org/telegram/ui/Components/AvatarsDrawable.java`
- `org/telegram/ui/Components/AvatarsListDrawable.java`
- `org/telegram/ui/Components/BackButtonMenu.java`
- `org/telegram/ui/Components/BlockingUpdateView.java`
- `org/telegram/ui/Components/Bulletin.java`
- `org/telegram/ui/Components/BulletinFactory.java`
- `org/telegram/ui/Components/CaptionPhotoViewer.java`
- `org/telegram/ui/Components/ChatActivityEnterView.java`
- `org/telegram/ui/Components/ChatAttachAlert.java`
- `org/telegram/ui/Components/ChatAttachAlertContactsLayout.java`
- `org/telegram/ui/Components/ChatAttachAlertDocumentLayout.java`
- `org/telegram/ui/Components/ChatAttachAlertPhotoLayout.java`
- `org/telegram/ui/Components/ChatAvatarContainer.java`
- `org/telegram/ui/Components/ChatGreetingsView.java`
- `org/telegram/ui/Components/ChatNotificationsPopupWrapper.java`
- `org/telegram/ui/Components/CircularProgressDrawable.java`
- `org/telegram/ui/Components/Crop/CropRotationWheel.java`
- `org/telegram/ui/Components/EarListener.java`
- `org/telegram/ui/Components/EditTextBoldCursor.java`
- `org/telegram/ui/Components/EditTextCaption.java`
- `org/telegram/ui/Components/EditTextEffects.java`
- `org/telegram/ui/Components/EditTextEmoji.java`
- `org/telegram/ui/Components/EmojiPacksAlert.java`
- `org/telegram/ui/Components/EmojiTabsStrip.java`
- `org/telegram/ui/Components/EmojiView.java`
- `org/telegram/ui/Components/FilterTabsView.java`
- `org/telegram/ui/Components/FragmentContextView.java`
- `org/telegram/ui/Components/FragmentFloatingButton.java`
- `org/telegram/ui/Components/FragmentSearchField.java`
- `org/telegram/ui/Components/GroupCallFullscreenAdapter.java`
- `org/telegram/ui/Components/GroupCallPip.java`
- `org/telegram/ui/Components/GroupCallPipAlertView.java`
- `org/telegram/ui/Components/GroupCreateSpan.java`
- `org/telegram/ui/Components/ImageUpdater.java`
- `org/telegram/ui/Components/InstantCameraView.java`
- `org/telegram/ui/Components/InstantCameraView2.java`
- `org/telegram/ui/Components/InstantCameraViewBase.java`
- `org/telegram/ui/Components/ItemOptions.java`
- `org/telegram/ui/Components/JoinCallByUrlAlert.java`
- `org/telegram/ui/Components/JoinGroupAlert.java`
- `org/telegram/ui/Components/LineProgressView.java`
- `org/telegram/ui/Components/MarkdownParser.java`
- `org/telegram/ui/Components/MediaActionDrawable.java`
- `org/telegram/ui/Components/MentionsContainerView.java`
- `org/telegram/ui/Components/MessagePreviewView.java`
- `org/telegram/ui/Components/Paint/Views/StickerMakerView.java`
- `org/telegram/ui/Components/Paint/Views/TextPaintView.java`
- `org/telegram/ui/Components/PaintingOverlay.java`
- `org/telegram/ui/Components/PasscodeView.java`
- `org/telegram/ui/Components/PhonebookShareAlert.java`
- `org/telegram/ui/Components/PhotoFilterView.java`
- `org/telegram/ui/Components/PhotoViewerCaptionEnterView.java`
- `org/telegram/ui/Components/PhotoViewerWebView.java`
- `org/telegram/ui/Components/PollVotesAlert.java`
- `org/telegram/ui/Components/Premium/AdaptiveIconImageView.java`
- `org/telegram/ui/Components/Premium/GLIcon/Icon3D.java`
- `org/telegram/ui/Components/Premium/LimitReachedBottomSheet.java`
- `org/telegram/ui/Components/Premium/PremiumAppIconsPreviewView.java`
- `org/telegram/ui/Components/Premium/PremiumGiftHeaderCell.java`
- `org/telegram/ui/Components/Premium/boosts/cells/selector/SelectorUserCell.java`
- `org/telegram/ui/Components/ProfileActionsView.java`
- `org/telegram/ui/Components/ProfileMetaballView.java`
- `org/telegram/ui/Components/PullForegroundDrawable.java`
- `org/telegram/ui/Components/RadialProgress2.java`
- `org/telegram/ui/Components/RadialProgressView.java`
- `org/telegram/ui/Components/Reactions/ChatSelectionReactionMenuOverlay.java`
- `org/telegram/ui/Components/Reactions/CustomEmojiReactionsWindow.java`
- `org/telegram/ui/Components/Reactions/ReactionsEffectOverlay.java`
- `org/telegram/ui/Components/Reactions/ReactionsLayoutInBubble.java`
- `org/telegram/ui/Components/ReactionsContainerLayout.java`
- `org/telegram/ui/Components/RecyclerListView.java`
- `org/telegram/ui/Components/ReplyMessageLine.java`
- `org/telegram/ui/Components/RichWidgetBlock.java`
- `org/telegram/ui/Components/SearchViewPager.java`
- `org/telegram/ui/Components/SectionsScrollView.java`
- `org/telegram/ui/Components/SeekBar.java`
- `org/telegram/ui/Components/SeekBarView.java`
- `org/telegram/ui/Components/SenderSelectPopup.java`
- `org/telegram/ui/Components/SenderSelectView.java`
- `org/telegram/ui/Components/ShareAlert.java`
- `org/telegram/ui/Components/SharedMediaLayout.java`
- `org/telegram/ui/Components/SimpleAvatarView.java`
- `org/telegram/ui/Components/SlideChooseView.java`
- `org/telegram/ui/Components/StatusBadgeComponent.java`
- `org/telegram/ui/Components/StickersAlert.java`
- `org/telegram/ui/Components/SuggestEmojiView.java`
- `org/telegram/ui/Components/Switch.java`
- `org/telegram/ui/Components/TextStyleSpan.java`
- `org/telegram/ui/Components/TopicsSidePanel.java`
- `org/telegram/ui/Components/TopicsTabsView.java`
- `org/telegram/ui/Components/TranscribeButton.java`
- `org/telegram/ui/Components/TranslateAlert2.java`
- `org/telegram/ui/Components/TranslateButton.java`
- `org/telegram/ui/Components/UItem.java`
- `org/telegram/ui/Components/UndoView.java`
- `org/telegram/ui/Components/UniversalAdapter.java`
- `org/telegram/ui/Components/UniversalRecyclerView.java`
- `org/telegram/ui/Components/VideoPlayer.java`
- `org/telegram/ui/Components/VideoPlayerSeekBar.java`
- `org/telegram/ui/Components/ViewPagerFixed.java`
- `org/telegram/ui/Components/WallpaperUpdater.java`
- `org/telegram/ui/Components/WidgetInlinePreview.java`
- `org/telegram/ui/Components/blur3/BlurredBackgroundWithFadeDrawable.java`
- `org/telegram/ui/Components/blur3/StrokeDrawable.java`
- `org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java`
- `org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java`
- `org/telegram/ui/Components/chat/buttons/ChatActivityBlurredRoundButton.java`
- `org/telegram/ui/Components/glass/GlassTabView.java`
- `org/telegram/ui/Components/quickforward/QuickShareAvatarCell.java`
- `org/telegram/ui/Components/quickforward/QuickShareSelectorDrawable.java`
- `org/telegram/ui/ContactAddActivity.java`
- `org/telegram/ui/ContactsActivity.java`
- `org/telegram/ui/ContentPreviewViewer.java`
- `org/telegram/ui/DataUsage2Activity.java`
- `org/telegram/ui/Delegates/MemberRequestsDelegate.java`
- `org/telegram/ui/DialogsActivity.java`
- `org/telegram/ui/EditWidgetActivity.java`
- `org/telegram/ui/EmojiAnimationsOverlay.java`
- `org/telegram/ui/FilterCreateActivity.java`
- `org/telegram/ui/FiltersSetupActivity.java`
- `org/telegram/ui/FragmentUsernameBottomSheet.java`
- `org/telegram/ui/Gifts/GiftSheet.java`
- `org/telegram/ui/Gifts/ProfileGiftsContainer.java`
- `org/telegram/ui/Gifts/ResaleGiftsFragment.java`
- `org/telegram/ui/GradientHeaderActivity.java`
- `org/telegram/ui/GroupCallActivity.java`
- `org/telegram/ui/GroupCreateFinalActivity.java`
- `org/telegram/ui/IntroActivity.java`
- `org/telegram/ui/InviteContactsActivity.java`
- `org/telegram/ui/LanguageSelectActivity.java`
- `org/telegram/ui/LaunchActivity.java`
- `org/telegram/ui/LinkEditActivity.java`
- `org/telegram/ui/LinkManager.java`
- `org/telegram/ui/LiteModeSettingsActivity.java`
- `org/telegram/ui/LocationActivity.java`
- `org/telegram/ui/LoginActivity.java`
- `org/telegram/ui/MainTabsActivity.java`
- `org/telegram/ui/MessageSeenView.java`
- `org/telegram/ui/NewContactBottomSheet.java`
- `org/telegram/ui/NotificationsSettingsActivity.java`
- `org/telegram/ui/OAuthSheet.java`
- `org/telegram/ui/PasskeysActivity.java`
- `org/telegram/ui/PassportActivity.java`
- `org/telegram/ui/PeerColorActivity.java`
- `org/telegram/ui/PhotoAlbumPickerActivity.java`
- `org/telegram/ui/PhotoPickerActivity.java`
- `org/telegram/ui/PhotoViewer.java`
- `org/telegram/ui/PopupNotificationActivity.java`
- `org/telegram/ui/PrivacyControlActivity.java`
- `org/telegram/ui/ProfileActivity.java`
- `org/telegram/ui/ProxyListActivity.java`
- `org/telegram/ui/ProxySettingsActivity.java`
- `org/telegram/ui/QrShare/QrGlass.java`
- `org/telegram/ui/QrShare/QrShareView.java`
- `org/telegram/ui/QrShare/RimPainter.java`
- `org/telegram/ui/RestrictedLanguagesSelectActivity.java`
- `org/telegram/ui/RightSlidingDialogContainer.java`
- `org/telegram/ui/SelectAnimatedEmojiDialog.java`
- `org/telegram/ui/SessionBottomSheet.java`
- `org/telegram/ui/SettingsActivity.java`
- `org/telegram/ui/Stars/BotStarsActivity.java`
- `org/telegram/ui/Stars/StarsIntroActivity.java`
- `org/telegram/ui/Stars/StarsReactionsSheet.java`
- `org/telegram/ui/StickersActivity.java`
- `org/telegram/ui/Stories/DialogStoriesCell.java`
- `org/telegram/ui/Stories/PeerStoriesView.java`
- `org/telegram/ui/Stories/ProfileStoriesView.java`
- `org/telegram/ui/Stories/StoriesController.java`
- `org/telegram/ui/Stories/StoriesUtilities.java`
- `org/telegram/ui/Stories/StoryViewer.java`
- `org/telegram/ui/Stories/recorder/CaptionContainerView.java`
- `org/telegram/ui/Stories/recorder/DualCameraView.java`
- `org/telegram/ui/Stories/recorder/SelectPeerView.java`
- `org/telegram/ui/Stories/recorder/StoryPrivacyBottomSheet.java`
- `org/telegram/ui/Stories/recorder/StoryPrivacySelector.java`
- `org/telegram/ui/Stories/recorder/StoryRecorder.java`
- `org/telegram/ui/Stories/recorder/Weather.java`
- `org/telegram/ui/TON/TONIntroActivity.java`
- `org/telegram/ui/ThemeActivity.java`
- `org/telegram/ui/TopicCreateFragment.java`
- `org/telegram/ui/TopicsFragment.java`
- `org/telegram/ui/UserInfoActivity.java`
- `org/telegram/ui/UsersSelectActivity.java`
- `org/telegram/ui/ViewPagerActivity.java`
- `org/telegram/ui/VoIPFragment.java`
- `org/telegram/ui/WearAuthSheet.java`
- `org/telegram/ui/bots/BotVerifySheet.java`
- `org/telegram/ui/bots/ChannelAffiliateProgramsFragment.java`
- `org/telegram/ui/community/CommunityCreateActivity.java`
- `org/telegram/ui/community/CommunityEditActivity.java`
- `org/telegram/ui/community/CommunitySheet.java`
- `org/telegram/ui/community/cells/CommunityLinkView.java`
- `org/telegram/ui/community/cells/CommunityLinkView2.java`
- `org/telegram/ui/iv/ChatAttachAlertRichLayout.java`
- `org/telegram/ui/iv/RichEditor.java`
- `org/telegram/ui/iv/RichEditorToolbar.java`
- `org/telegram/ui/web/BotWebViewContainer.java`
- `org/telegram/ui/web/BrowserHistory.java`
- `org/telegram/ui/web/SearchEngine.java`
- `org/telegram/ui/web/WebActionBar.java`
- `org/telegram/utils/glass/BaseFragmentSimpleGlass.java`
- `org/telegram/utils/glass/fade/GlassFadeBlurredDrawable.java`
- `org/telegram/utils/recorder/round/RoundVideoCameraController.java`
- `org/telegram/utils/recorder/round/RoundVideoCameraXController.java`
- `org/telegram/utils/twidget/WidgetMedia.java`

</details>
