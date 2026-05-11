# TekSphere — EMS React Native (Expo) Mobile App

> Employee Management System mobile application built with **React Native** and **Expo SDK 54**, using **Expo Router** for file-based navigation.

---

## 📋 Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| **Node.js** | >= 18.x | JavaScript runtime |
| **npm** | >= 9.x *(ships with Node)* | Package manager |
| **Expo CLI** | Latest | Local dev server (`npx expo`) |
| **EAS CLI** | >= 13.0.0 | Cloud builds & submissions |
| **Expo Account** | — | Required to run EAS builds |
| **Git** | Latest | Version control |

### Optional (for local emulator testing)

| Requirement | Notes |
|---|---|
| **Android Studio** | Includes Android SDK & AVD emulator |
| **Expo Go** (mobile app) | Quick testing on a physical device |

---

## 🚀 Getting Started (Local Development)

### 1. Install Dependencies

```bash
cd employeemanagementsystem/ems-frontendNative
npm install
```

### 2. Configure Environment

Create a `.env` file in the project root (if not already present):

```env
EXPO_PUBLIC_API_URL=https://ems-backend-zl35.onrender.com/api
```

> **Note:** Change this URL to your local backend (e.g. `http://<YOUR_IP>:8000/api`) during local development if needed.

### 3. Start the Dev Server

```bash
npx expo start
```

This will open the **Expo DevTools** in your terminal. From here you can:

- Press **`a`** — open in Android emulator
- Press **`i`** — open in iOS simulator (macOS only)
- Press **`w`** — open in web browser
- Scan the **QR code** with the **Expo Go** app on your phone

---

## 📦 Building the APK / Application with EAS

Expo Application Services (EAS) is used to build production-ready binaries in the cloud — **no Android Studio or local SDK required**.

### Step 1 — Install EAS CLI

```bash
npm install -g eas-cli
```

### Step 2 — Log in to your Expo Account

```bash
eas login
```

> You will be prompted for your Expo username and password. Create an account at [expo.dev](https://expo.dev) if you don't have one.

### Step 3 — Verify Project Configuration

Ensure the following files are correctly configured (they are already set up in this repo):

- **`app.json`** — App name, slug, Android package name (`com.tektalis.ems`), icon, splash screen.
- **`eas.json`** — Build profiles and environment variables for each environment.

### Step 4 — Build the APK

#### 🔹 Preview APK (recommended for testing / internal distribution)

```bash
eas build --platform android --profile preview
```

#### 🔹 Production APK

```bash
eas build --platform android --profile production
```

#### 🔹 Development Build (includes dev-client for debugging)

```bash
eas build --platform android --profile development
```

> **What happens:** EAS uploads your project to Expo's cloud build servers, compiles the native Android binary, and provides a download link when finished. No local Android SDK is needed.

### Step 5 — Download & Install the APK

Once the build completes:

1. Visit the build URL printed in your terminal, **or** go to [expo.dev](https://expo.dev) → your project → Builds.
2. Download the `.apk` file.
3. Transfer it to your Android device and install it (you may need to enable **"Install from unknown sources"** in your device settings).

---

## 🔧 EAS Build Profiles Reference

The `eas.json` defines three build profiles:

| Profile | Output | Distribution | Use Case |
|---|---|---|---|
| `development` | Dev Client build | Internal | Debugging with `expo-dev-client` |
| `preview` | `.apk` | Internal | Testing / sharing with team |
| `production` | `.apk` | Public / Internal | Final release-ready build |

All profiles inject the production API URL via the `EXPO_PUBLIC_API_URL` environment variable.

---

## 🍎 iOS Builds (Optional)

To build for iOS, you need an **Apple Developer Account** ($99/year).

```bash
eas build --platform ios --profile production
```

> iOS builds produce an `.ipa` file. Distribution to devices requires either TestFlight or Ad Hoc provisioning.

---

## 📂 Project Structure

```
ems-frontendNative/
├── app/                  # Expo Router file-based routes
├── src/
│   ├── assets/           # Icons, splash images, logos
│   ├── components/       # Reusable UI components
│   ├── services/         # API service layer (Axios)
│   └── ...
├── app.json              # Expo app configuration
├── eas.json              # EAS Build profiles
├── babel.config.js       # Babel configuration
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies & scripts
└── .env                  # Environment variables (local)
```

---

## 📝 Available Scripts

| Command | Description |
|---|---|
| `npm start` | Start Expo dev server |
| `npm run android` | Run on Android emulator |
| `npm run ios` | Run on iOS simulator |
| `npm run web` | Run in web browser |

---

## ⚠️ Troubleshooting

| Issue | Solution |
|---|---|
| `eas: command not found` | Run `npm install -g eas-cli` |
| Build fails with dependency errors | Delete `node_modules` and `package-lock.json`, then run `npm install` |
| APK can't connect to backend | Verify `EXPO_PUBLIC_API_URL` in `eas.json` matches your deployed backend URL |
| Android emulator not detected | Ensure Android Studio's `platform-tools` is in your system `PATH` |
| QR code not working on Expo Go | Ensure your phone and dev machine are on the **same Wi-Fi network** |

---

## 🔗 Useful Links

- [Expo Documentation](https://docs.expo.dev)
- [EAS Build Guide](https://docs.expo.dev/build/introduction/)
- [Expo Router Docs](https://docs.expo.dev/router/introduction/)
- [React Native Docs](https://reactnative.dev)
