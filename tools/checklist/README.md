```
npm create vite@latest
```

```shell
PS D:\Github\LLM\ScoreAggregationManager> npm create vite@latest Need to install the following packages: create-vite@8.3.0 Ok to proceed? (y) y > npx > create-vite │ ◆ Project name: │ vite-project └
```

みたいに聞かれたら、適当にプロジェクト名を付ける。

```
SAM-UI
```

```shell
Select a framework:
```
に対しては
```
React
```
を選択。

```shell
Select a variant:
```
に対しては
```
TypeScript
```
を選ぶ。

```shell
◆  Use Vite 8 beta (Experimental)?:
│  ○ Yes
│  ● No
└
```
と聞かれたらNoで進める。

```shell
│
◆  Install with npm and start now?
│  ● Yes / ○ No
└
```
と聞かれたらYesで。
これを選ぶと
```
npm install
npm run dev
```
まで勝手にやってくれる。

installが終わると、フォルダが作られる。
```
cd SAM-UI
```
と聞かれたらOKで。

```shell

  VITE v7.3.1  ready in 740 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```
が出たらURL遷移。
表示されてたら立ち上げ成功。

```
SAM-UI
  └ src
      └ App.tsx
```
に遷移して、tsxの中身を好きなコードに変える。

### Tailwindを使っている場合
```
className="flex ..."
className="grid ..."
className="bg-gray-..."
className="p-4 ..."
```
みたいなコードを使用している場合、
↑で作成したプロジェクト内のターミナルを開き、下記を実行。

```shell
npm uninstall tailwindcss
npm install -D tailwindcss@3.4.4 postcss autoprefixer
```
npxコマンドがエラーを吐いた場合手動で何とかする。
プロジェクト直下にtailwind.config.jsを作成。

```JS
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

同じ階層に
postcss.config.js 作成

```JS
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

src/index.css をこれに置き換え
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

ダメなら
```shell
```shell
npm uninstall tailwindcss
npm install -D tailwindcss@3.4.4 postcss autoprefixer
```

はい起動。