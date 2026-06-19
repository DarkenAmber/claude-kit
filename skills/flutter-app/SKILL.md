---
name: flutter-app
description: Build Flutter mobile applications with clean architecture, offline-first approach, and Google Drive sync. Use when building Android apps, cross-platform mobile tools, or Flutter web apps.
tags:
  - flutter
  - dart
  - android
  - mobile
  - offline
  - google-drive
  - cross-platform
version: 1.2
---

# Flutter App - Claude Skill

> Android first. Offline first. Simple architecture.
> Build Flutter apps that work without internet, sync through Google Drive, and run on any Android device.

---

## When to Use This Skill

Use when:
- Building a Flutter Android app from scratch
- Adding Google Drive sync to an existing app
- Choosing architecture for a new Flutter project
- Building offline-first mobile tools
- Creating apps for non-technical users (business owners, field workers, small teams)

Do NOT use when:
- Building web-only apps (use single-file-app skill instead)
- iOS is the primary target (this skill is Android-first)
- The app requires cloud real-time backend (Firebase RTDB, Firestore live sync)
- Building games or graphics-heavy apps

> **Note:** Local WebSocket to hardware (ESP32, IoT devices) is fine and common.
> What to avoid is cloud real-time backend dependency, not WebSocket itself.

---

## Core Philosophy

An app that works without internet is always better than one that requires it.
Simple state management beats clever architecture every time.
Build for your actual users - not for other developers.

---

## Rules

### 1. Android first, web second
- Target Android as primary platform
- Flutter Web as bonus - same codebase, free deployment
- Never block development waiting for iOS setup
- Test on real Android device, not just emulator

### 2. Offline first - always
- All core features must work without internet
- Use local storage (Hive, SharedPreferences, SQLite) for all data
- Network sync is enhancement, not requirement
- Show cached data immediately, sync in background

### 3. Simple architecture - no over-engineering
- StatefulWidget for simple local state
- Provider for shared state across screens
- Riverpod only when Provider is genuinely insufficient
- Bloc/Cubit only for complex async flows - not by default
- No architecture astronautics for simple apps

### 4. Google Drive as backend
- Use Google Drive API for cloud sync - free, reliable, no server needed
- Each user syncs to their own Drive folder (personal backup)
- For team access: use shared folder via Drive permissions with broader scope
- Never build your own backend when Drive works

### 5. Ask before big refactors
- Never silently change working widget structure
- Ask before switching state management approach
- "It works" beats "it's architecturally pure"

---

## Project Structure

```
lib/
├── main.dart
├── app/
│   ├── app.dart              # MaterialApp, theme, routing
│   └── routes.dart           # GoRouter configuration
├── features/
│   ├── home/
│   │   ├── screens/
│   │   ├── widgets/
│   │   └── providers/
│   └── settings/
│       ├── screens/
│       └── providers/
├── shared/
│   ├── widgets/              # Reusable UI components
│   ├── models/               # Data models
│   ├── services/             # Drive, storage, auth
│   └── theme/                # Colors, typography
└── core/
    ├── constants.dart
    └── extensions.dart
```

Feature-first, not layer-first. Each feature is self-contained.

---

## State Management

### Default: Provider
For most apps, Provider is enough:

```dart
class CarProvider extends ChangeNotifier {
  List<Car> _cars = [];
  List<Car> get cars => _cars;

  void addCar(Car car) {
    _cars.add(car);
    notifyListeners();
    _save();
  }

  Future<void> _save() async {
    // save to local storage
  }
}
```

### When to use Riverpod
Only when you need:
- Computed state from multiple providers
- Auto-dispose of expensive resources
- Code generation for large apps (50+ screens)

### Never use Bloc for simple CRUD
Bloc adds complexity without benefit for basic create/read/update/delete flows.

---

## Navigation

Always use GoRouter:

```dart
final router = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(
      path: '/car/:id',
      builder: (ctx, state) =>
        CarDetailScreen(id: state.pathParameters['id']!),
    ),
  ],
);
```

Never use Navigator.push directly for named routes.

---

## Local Storage

### Hive - for structured data
```dart
@HiveType(typeId: 0)
class Car extends HiveObject {
  @HiveField(0) late String id;
  @HiveField(1) late String plate;
  @HiveField(2) late String vin;
  @HiveField(3) late DateTime lastService;
}

// Usage
final box = Hive.box<Car>('cars');
box.put(car.id, car);
final cars = box.values.toList();
```

> **Note:** Hive is in maintenance mode. Consider Isar or Hive CE for new projects.
> For simple key-value: SharedPreferences is always fine.

### SharedPreferences - for settings
```dart
final prefs = await SharedPreferences.getInstance();
prefs.setString('currency', 'AZN');
final currency = prefs.getString('currency') ?? 'AZN';
```

---

## Google Drive Sync

### GoogleAuthClient helper (required)
```dart
import 'package:googleapis/drive/v3.dart' as drive;
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:google_sign_in/google_sign_in.dart';

class GoogleAuthClient extends http.BaseClient {
  final Map<String, String> _headers;
  final http.Client _client = http.Client();

  GoogleAuthClient(this._headers);

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    return _client.send(request..headers.addAll(_headers));
  }
}
```

### Auth pattern (google_sign_in 7.x)
```dart
class DriveService {
  // Personal backup - access only to files created by this app
  static const _personalScopes = [drive.DriveApi.driveFileScope];

  // Team folder - access to shared folders
  static const _teamScopes = [drive.DriveApi.driveScope];

  drive.DriveApi? _driveApi;

  Future<bool> signIn({bool teamMode = false}) async {
    final scopes = teamMode ? _teamScopes : _personalScopes;

    // google_sign_in 7.x - singleton
    // initialize() takes no scopes - only sets up clientId if needed
    final googleSignIn = GoogleSignIn.instance;
    await googleSignIn.initialize();

    try {
      // Step 1: Authentication (who is the user)
      final account = await googleSignIn.authenticate();

      // Step 2: Authorization (Drive scope access) - separate step in v7
      // Check cached grant first to avoid unnecessary user prompts
      final authorization =
          await account.authorizationClient.authorizationForScopes(scopes)
          ?? await account.authorizationClient.authorizeScopes(scopes);

      // Step 3: Use accessToken from authorization, not authentication
      final client = GoogleAuthClient({
        'Authorization': 'Bearer ${authorization.accessToken}',
      });
      _driveApi = drive.DriveApi(client);
      return true;
    } on GoogleSignInException {
      // User cancelled or no access
      return false;
    }
  }
}
```

> **google_sign_in 7.x key changes:**
> - `initialize()` takes no scopes - scopes go to `authorizeScopes()`
> - `accessToken` removed from `authentication` - use `authorizationClient.authorizeScopes()`
> - `authentication` is now synchronous (no await needed for idToken)
> - `authenticate()` on Flutter Web is not supported - use platform button flow instead

> **OAuth verification warning:**
> - `driveFileScope` (personal mode) - no Google verification required
> - `driveScope` (team mode) - requires Google OAuth verification for Play Store apps,
>   including possible CASA security assessment. Plan for this before release.

### Upload file - correct byte length
```dart
Future<void> uploadFile(String name, String content, String folderId) async {
  // IMPORTANT: use bytes.length not content.length
  // content.length = char count, bytes.length = byte count
  // They differ for Cyrillic, Azerbaijani (ə ç ş ğ), and other non-ASCII
  final bytes = utf8.encode(content);
  final media = drive.Media(Stream.value(bytes), bytes.length);

  await _driveApi!.files.create(
    drive.File()..name = name..parents = [folderId],
    uploadMedia: media,
  );
}
```

### Sync strategy
- **Personal (driveFileScope):** app reads only files it created. Good for single-device backup.
- **Team (driveScope):** app can read shared folders. Needed for multi-user scenarios.
- Save locally first, sync when internet available
- Conflict resolution: last-write-wins for single-device only.
  For multi-device/team: store timestamp and warn user on conflict.

---

## Localization (AZ / EN / RU)

For apps targeting CIS + Azerbaijan market:

```yaml
# pubspec.yaml
dependencies:
  flutter_localizations:
    sdk: flutter
  # intl: pulled transitively via flutter_localizations
```

```dart
// app/app.dart
MaterialApp.router(
  localizationsDelegates: [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: const [
    Locale('az'), // Azerbaijani - primary
    Locale('en'), // English - secondary
    Locale('ru'), // Russian - CIS users
  ],
  ...
)
```

Structure:
```
lib/l10n/
├── app_az.arb   # Azerbaijani (primary)
├── app_en.arb   # English
└── app_ru.arb   # Russian
```

```json
// app_az.arb
{
  "appName": "AutoKit",
  "addCar": "Avtomobil əlavə et",
  "carPlate": "Nömrə nişanı"
}
```

Always add all three locales from the start. Adding them later is painful.

---

## Theme

Define theme once, never hardcode colors in widgets:

```dart
class AppTheme {
  // Define YOUR brand colors here - do not copy these values blindly
  static const Color primary   = Color(0xFF000000); // your primary
  static const Color accent    = Color(0xFF000000); // your accent
  static const Color surface   = Color(0xFF000000); // your surface
  static const Color onSurface = Color(0xFF000000); // text on surface

  static ThemeData dark() => ThemeData(
    colorScheme: ColorScheme.dark(
      primary: accent,
      surface: surface,
      onSurface: onSurface,
    ),
    useMaterial3: true,
    fontFamily: 'YourFont', // define your font
  );

  static ThemeData light() => ThemeData(
    colorScheme: ColorScheme.light(
      primary: accent,
    ),
    useMaterial3: true,
    fontFamily: 'YourFont',
  );
}
```

> Replace placeholder colors with your actual brand tokens.
> Never hardcode `Color(0xFF...)` directly in widgets.

---

## Performance Rules

- Use `const` constructors everywhere possible
- `ListView.builder` for lists - never `ListView` with children
- Avoid `Image.network` in offline-first apps - prefer cached assets
  If you must use network images, always provide offline fallback
- Avoid rebuilding entire widget tree - use `Consumer` or `Selector`
- Profile with Flutter DevTools before optimizing

---

## Camera and Scanning

For barcode/QR scanning:

```dart
MobileScanner(
  onDetect: (capture) {
    final barcode = capture.barcodes.first;
    final value = barcode.rawValue;
    if (value != null) onScanned(value);
  },
)
```

Always request camera permission before showing scanner.

---

## Permissions

```dart
final status = await Permission.camera.request();
if (status.isDenied) {
  // show explanation to user - never crash
  return;
}
```

Handle permission denial gracefully. Show explanation before requesting.

---

## Pre-ship Checklist

- [ ] App works fully offline (tested in airplane mode)
- [ ] Back button works on all screens
- [ ] App handles permission denial gracefully
- [ ] All user-visible strings use l10n (az/en/ru)
- [ ] Loading states shown for async operations
- [ ] Empty states shown when no data
- [ ] Error states shown with user-friendly message (not stack trace)
- [ ] Tested on real Android device (not just emulator)
- [ ] App icon and splash screen set
- [ ] Release build tested (not just debug)
- [ ] Drive sync tested with real Google account

---

## Anti-Patterns

- Never use Bloc for a simple counter or toggle
- Never Navigator.push for named routes - use GoRouter
- Never `setState` in initState - use addPostFrameCallback
- Never ignore `dispose()` - always cancel streams and controllers
- Never call `setState` after widget is disposed
- Never hardcode colors - use theme
- Never build UI in services - keep separation
- Never use `content.length` for Drive Media - use `bytes.length`
- Never use `Image.network` without offline fallback in offline-first apps

---

## Essential Packages

```yaml
dependencies:
  flutter:
    sdk: flutter
  go_router: ^14.0.0
  provider: ^6.1.0
  hive_flutter: ^1.1.0
  shared_preferences: ^2.2.0
  google_sign_in: ^7.0.0
  googleapis: ^13.0.0
  mobile_scanner: ^5.0.0
  permission_handler: ^11.0.0
  uuid: ^4.0.0
  http: ^1.2.0
  flutter_localizations:
    sdk: flutter
  # intl is pulled transitively via flutter_localizations
  # add directly only if using gen-l10n and pub complains

dev_dependencies:
  hive_generator: ^2.0.0
  build_runner: ^2.4.0
```

---

*Simple apps ship. Complex apps stay in development.*
