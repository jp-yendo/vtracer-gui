# vtracer-gui

VtracerのGUIアプリケーション - 画像をSVGに変換するPythonベースのデスクトップアプリケーション

## 概要

このプロジェクトは、画像ファイルをベクターグラフィック（SVG）に変換するためのグラフィカルユーザーインターフェースを提供します。バックエンドでRustベースのvtracerライブラリを使用し、フロントエンドはPyQt5で構築されています。

## 前提条件

### Rustのインストール

vtracerライブラリはRustで書かれているため、Rustのインストールが必要です。

1. [Rust公式サイト](https://rustup.rs/)にアクセス
2. rustupインストーラーをダウンロードして実行
3. インストール後、ターミナルで以下のコマンドを実行してインストールを確認：
   ```bash
   rustc --version
   cargo --version
   ```

### Pythonのインストール

- Python 3.7以上が必要です
- [Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストール

## 開発環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd vtracer-gui
```

### 2. Python仮想環境の作成

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 依存関係の詳細

- **PyQt5**: GUIフレームワーク
- **pyinstaller**: 実行可能ファイルの作成
- **vtracer**: 画像からSVGへの変換ライブラリ（Rustベース）

## 実行方法

### 開発モードでの実行

```bash
python vtracer-gui.py
```

## ビルド方法

### 実行可能ファイルの作成

**Windows:**
```powershell
.\make.ps1
```

**macOS/Linux:**
```bash
chmod +x make.sh
./make.sh
```

ビルドが完了すると、`dist`フォルダに実行可能ファイルが作成されます。
