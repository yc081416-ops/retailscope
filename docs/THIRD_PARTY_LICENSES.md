# 第三方许可与引用组件

核查日期：2026-11-13。以下依据锁定版本、已安装 Python 分发元数据与前端锁文件逐项记录；本项目不主张这些内容的版权，也不以根目录 MIT 替换其许可。

## 源码中引用的组件

`frontend/src/components/ui/button.tsx`、`badge.tsx` 及 `lib/utils.ts` 使用 shadcn/ui 的组件模式。保留以下上游 MIT 声明；作者自己的改动只在其拥有权利的范围内授权。

来源：[shadcn/ui LICENSE](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md)。

```text
MIT License

Copyright (c) 2023 shadcn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Python 锁定依赖

来源：`requirements-lock.txt`、`api/requirements-lock.txt` 与本机同版本 `*.dist-info/METADATA`、许可文件。长文本仅在下表归一为名称；完整条款仍以原分发中的 LICENSE/NOTICE 为准。

| 包 | 版本 | 许可声明 / 文件核对 |
|---|---|---|
| Jinja2 | 3.1.6 | BSD-3-Clause（分发许可正文） |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| PyYAML | 6.0.3 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| SQLAlchemy | 2.1.8 | MIT |
| altair | 6.3.0 | BSD-3-Clause（分发许可正文） |
| annotated-doc | 0.0.6 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.16.0 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.1 | BSD-3-Clause |
| colorama | 0.4.6 | BSD-3-Clause（分发许可正文） |
| fastapi | 0.162.5 | MIT |
| h11 | 0.16.0 | MIT |
| httpcore2 | 2.16.0 | BSD-3-Clause |
| httpx2 | 2.16.0 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| itsdangerous | 2.2.0 | BSD-3-Clause（分发许可正文） |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| kagglehub | 1.0.3 | Apache-2.0 |
| kagglesdk | 0.1.38 | Apache-2.0 |
| narwhals | 2.28.0 | MIT |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| opentelemetry-api | 1.45.2 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 2.3.3 | BSD-3-Clause（分发许可正文） |
| pillow | 13.0.0 | MIT-CMU |
| plotly | 6.9.0 | MIT |
| pluggy | 1.7.0 | MIT |
| protobuf | 7.36.2 | BSD-3-Clause |
| psycopg | 3.3.9 | LGPL-3.0-only |
| psycopg-binary | 3.3.9 | LGPL-3.0-only |
| pyarrow | 26.0.1 | Apache-2.0 |
| pydantic | 2.14.3 | MIT |
| pydantic_core | 2.50.4 | MIT |
| pydeck | 0.9.3 | Apache License 2.0 |
| pytest | 9.2.0 | MIT |
| python-dateutil | 4.0.0 | BSD-3-Clause |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| python-multipart | 0.0.33 | Apache-2.0 |
| pytz | 2026.6 | MIT |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rpds-py | 2026.9.1 | MIT |
| scipy | 1.18.1 | BSD-3-Clause（分发许可正文） |
| starlette | 1.10.0 | BSD-3-Clause |
| streamlit | 1.67.0 | Apache-2.0 |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| truststore | 0.10.5 | MIT |
| typing-inspection | 0.4.5 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.6 | Apache-2.0 |
| urllib3 | 2.8.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| watchdog | 7.1.0 | Apache-2.0 |
| websockets | 17.4 | BSD-3-Clause |

## 前端完整锁文件依赖

包括运行、开发、传递及平台可选包；锁文件声明不等于逐个审查其内嵌的全部第三方子组件。安装后保留包内 LICENSE/NOTICE；不随源码仓库打包 node_modules 或构建产物。

| 锁文件包路径 | 版本 | 声明许可 |
|---|---|---|
| `node_modules/@emnapi/core` | 2.0.0-beta.2 | MIT |
| `node_modules/@emnapi/runtime` | 2.0.0-beta.2 | MIT |
| `node_modules/@emnapi/wasi-threads` | 2.2.0 | MIT |
| `node_modules/@floating-ui/core` | 1.8.0 | MIT |
| `node_modules/@floating-ui/dom` | 1.8.0 | MIT |
| `node_modules/@floating-ui/react-dom` | 2.1.9 | MIT |
| `node_modules/@floating-ui/utils` | 0.2.12 | MIT |
| `node_modules/@jridgewell/gen-mapping` | 0.3.13 | MIT |
| `node_modules/@jridgewell/remapping` | 2.3.5 | MIT |
| `node_modules/@jridgewell/resolve-uri` | 3.1.3 | MIT |
| `node_modules/@jridgewell/sourcemap-codec` | 1.6.0 | MIT |
| `node_modules/@jridgewell/trace-mapping` | 0.3.31 | MIT |
| `node_modules/@napi-rs/wasm-runtime` | 1.2.6 | MIT |
| `node_modules/@oxc-project/types` | 0.156.0 | MIT |
| `node_modules/@radix-ui/number` | 1.1.3 | MIT |
| `node_modules/@radix-ui/primitive` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-accessible-icon` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-accordion` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-alert-dialog` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-arrow` | 1.1.17 | MIT |
| `node_modules/@radix-ui/react-aspect-ratio` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-avatar` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-checkbox` | 1.4.1 | MIT |
| `node_modules/@radix-ui/react-collapsible` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-collection` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-compose-refs` | 1.1.5 | MIT |
| `node_modules/@radix-ui/react-context` | 1.3.0 | MIT |
| `node_modules/@radix-ui/react-context-menu` | 2.4.1 | MIT |
| `node_modules/@radix-ui/react-dialog` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-direction` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-dismissable-layer` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-dropdown-menu` | 2.2.1 | MIT |
| `node_modules/@radix-ui/react-focus-guards` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-focus-scope` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-form` | 0.3.0 | MIT |
| `node_modules/@radix-ui/react-hover-card` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-id` | 1.1.4 | MIT |
| `node_modules/@radix-ui/react-label` | 2.1.17 | MIT |
| `node_modules/@radix-ui/react-menu` | 2.2.1 | MIT |
| `node_modules/@radix-ui/react-menubar` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-navigation-menu` | 1.4.1 | MIT |
| `node_modules/@radix-ui/react-one-time-password-field` | 0.2.1 | MIT |
| `node_modules/@radix-ui/react-password-toggle-field` | 0.2.1 | MIT |
| `node_modules/@radix-ui/react-popover` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-popper` | 1.4.0 | MIT |
| `node_modules/@radix-ui/react-portal` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-presence` | 1.1.11 | MIT |
| `node_modules/@radix-ui/react-primitive` | 2.2.0 | MIT |
| `node_modules/@radix-ui/react-progress` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-radio-group` | 1.5.1 | MIT |
| `node_modules/@radix-ui/react-roving-focus` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-scroll-area` | 1.4.0 | MIT |
| `node_modules/@radix-ui/react-select` | 2.4.1 | MIT |
| `node_modules/@radix-ui/react-separator` | 1.2.0 | MIT |
| `node_modules/@radix-ui/react-slider` | 1.6.1 | MIT |
| `node_modules/@radix-ui/react-slot` | 1.5.0 | MIT |
| `node_modules/@radix-ui/react-switch` | 1.4.1 | MIT |
| `node_modules/@radix-ui/react-tabs` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-toast` | 1.3.1 | MIT |
| `node_modules/@radix-ui/react-toggle` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-toggle-group` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-toolbar` | 1.2.1 | MIT |
| `node_modules/@radix-ui/react-tooltip` | 1.4.1 | MIT |
| `node_modules/@radix-ui/react-use-callback-ref` | 1.1.5 | MIT |
| `node_modules/@radix-ui/react-use-controllable-state` | 1.3.0 | MIT |
| `node_modules/@radix-ui/react-use-effect-event` | 0.0.5 | MIT |
| `node_modules/@radix-ui/react-use-escape-keydown` | 1.1.6 | MIT |
| `node_modules/@radix-ui/react-use-is-hydrated` | 0.1.3 | MIT |
| `node_modules/@radix-ui/react-use-layout-effect` | 1.1.4 | MIT |
| `node_modules/@radix-ui/react-use-previous` | 1.1.4 | MIT |
| `node_modules/@radix-ui/react-use-rect` | 1.1.4 | MIT |
| `node_modules/@radix-ui/react-use-size` | 1.1.5 | MIT |
| `node_modules/@radix-ui/react-visually-hidden` | 1.2.13 | MIT |
| `node_modules/@radix-ui/rect` | 1.1.3 | MIT |
| `node_modules/@rolldown/binding-android-arm-eabi` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-android-arm64` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-darwin-arm64` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-darwin-x64` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-freebsd-x64` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-arm-gnueabihf` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-arm64-gnu` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-arm64-musl` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-ppc64-gnu` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-s390x-gnu` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-x64-gnu` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-linux-x64-musl` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-openharmony-arm64` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-wasm32-wasi` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-win32-arm64-msvc` | 1.2.19 | MIT |
| `node_modules/@rolldown/binding-win32-x64-msvc` | 1.2.19 | MIT |
| `node_modules/@rolldown/pluginutils` | 1.1.0 | MIT |
| `node_modules/@tailwindcss/node` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-android-arm64` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-darwin-arm64` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-darwin-x64` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-freebsd-x64` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-linux-arm-gnueabihf` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-linux-arm64-gnu` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-linux-arm64-musl` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-linux-x64-gnu` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-linux-x64-musl` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/core` | 1.11.3 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/runtime` | 1.11.3 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/wasi-threads` | 1.2.3 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@napi-rs/wasm-runtime` | 1.2.2 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@tybys/wasm-util` | 0.10.3 | MIT |
| `node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/tslib` | 2.8.1 | 0BSD |
| `node_modules/@tailwindcss/oxide-win32-arm64-msvc` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/oxide-win32-x64-msvc` | 4.3.5 | MIT |
| `node_modules/@tailwindcss/vite` | 4.3.5 | MIT |
| `node_modules/@tybys/wasm-util` | 0.10.4 | MIT |
| `node_modules/@types/chai` | 5.2.3 | MIT |
| `node_modules/@types/deep-eql` | 4.0.2 | MIT |
| `node_modules/@types/estree` | 1.0.10 | MIT |
| `node_modules/@types/node` | 26.6.6 | MIT |
| `node_modules/@types/react` | 19.3.0 | MIT |
| `node_modules/@types/react-dom` | 19.3.0 | MIT |
| `node_modules/@typescript/typescript-aix-ppc64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-darwin-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-darwin-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-freebsd-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-freebsd-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-arm` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-loong64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-mips64el` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-ppc64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-riscv64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-s390x` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-linux-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-netbsd-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-netbsd-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-openbsd-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-openbsd-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-sunos-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-win32-arm64` | 7.0.2 | Apache-2.0 |
| `node_modules/@typescript/typescript-win32-x64` | 7.0.2 | Apache-2.0 |
| `node_modules/@vitejs/plugin-react` | 6.3.0 | MIT |
| `node_modules/@vitest/mocker` | 5.1.0 | MIT |
| `node_modules/@vitest/spy` | 5.1.0 | MIT |
| `node_modules/aria-hidden` | 1.2.6 | MIT |
| `node_modules/assertion-error` | 2.0.1 | MIT |
| `node_modules/chai` | 6.3.0 | MIT |
| `node_modules/class-variance-authority` | 0.7.1 | Apache-2.0 |
| `node_modules/clsx` | 2.1.1 | MIT |
| `node_modules/cn` | 0.5.2 | MIT |
| `node_modules/csstype` | 3.2.3 | MIT |
| `node_modules/detect-libc` | 2.1.2 | Apache-2.0 |
| `node_modules/detect-node-es` | 1.1.0 | MIT |
| `node_modules/echarts` | 6.1.0 | Apache-2.0 |
| `node_modules/echarts/node_modules/tslib` | 2.3.0 | 0BSD |
| `node_modules/enhanced-resolve` | 5.27.0 | MIT |
| `node_modules/es-module-lexer` | 2.3.2 | MIT |
| `node_modules/estree-walker` | 3.0.3 | MIT |
| `node_modules/expect-type` | 1.4.0 | Apache-2.0 |
| `node_modules/fdir` | 6.5.0 | MIT |
| `node_modules/fsevents` | 2.3.3 | MIT |
| `node_modules/get-nonce` | 1.0.1 | MIT |
| `node_modules/graceful-fs` | 4.2.12 | BlueOak-1.0.0 |
| `node_modules/jiti` | 2.7.0 | MIT |
| `node_modules/lightningcss` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-android-arm64` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-darwin-arm64` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-darwin-x64` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-freebsd-x64` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-linux-arm-gnueabihf` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-linux-arm64-gnu` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-linux-arm64-musl` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-linux-x64-gnu` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-linux-x64-musl` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-win32-arm64-msvc` | 1.33.0 | MPL-2.0 |
| `node_modules/lightningcss-win32-x64-msvc` | 1.33.0 | MPL-2.0 |
| `node_modules/lucide-react` | 1.72.0 | ISC |
| `node_modules/magic-string` | 1.4.5 | MIT |
| `node_modules/nanoid` | 3.3.20 | MIT |
| `node_modules/obug` | 3.0.0 | MIT |
| `node_modules/picocolors` | 1.1.1 | ISC |
| `node_modules/picomatch` | 4.0.7 | MIT |
| `node_modules/postcss` | 8.5.32 | MIT |
| `node_modules/radix-ui` | 1.8.1 | MIT |
| `node_modules/react` | 19.3.1 | MIT |
| `node_modules/react-dom` | 19.3.1 | MIT |
| `node_modules/react-remove-scroll` | 2.7.2 | MIT |
| `node_modules/react-remove-scroll-bar` | 2.3.8 | MIT |
| `node_modules/react-style-singleton` | 2.2.3 | MIT |
| `node_modules/rolldown` | 1.2.19 | MIT |
| `node_modules/scheduler` | 0.28.0 | MIT |
| `node_modules/source-map-js` | 1.2.2 | BSD-3-Clause |
| `node_modules/std-env` | 4.3.0 | MIT |
| `node_modules/tailwind-merge` | 3.7.0 | MIT |
| `node_modules/tailwindcss` | 4.3.5 | MIT |
| `node_modules/tapable` | 2.3.3 | MIT |
| `node_modules/tinybench` | 6.2.3 | MIT |
| `node_modules/tinyexec` | 1.3.1 | MIT |
| `node_modules/tinyglobby` | 0.2.17 | MIT |
| `node_modules/tslib` | 2.9.1 | 0BSD |
| `node_modules/typescript` | 7.0.2 | Apache-2.0 |
| `node_modules/undici-types` | 8.9.0 | MIT |
| `node_modules/use-callback-ref` | 1.3.3 | MIT |
| `node_modules/use-sidecar` | 1.1.3 | MIT |
| `node_modules/vite` | 8.3.8 | MIT |
| `node_modules/vitest` | 5.1.0 | MIT |
| `node_modules/why-is-node-running` | 3.2.1 | MIT |
| `node_modules/zrender` | 6.1.0 | BSD-3-Clause |
| `node_modules/zrender/node_modules/tslib` | 2.3.0 | 0BSD |

## 特别说明与后续分发检查

- `lucide-react` 图标含 Lucide ISC 与部分 Feather MIT 权利声明，完整通知位于安装包 LICENSE；不能把它们当作作者原创图形。
- NumPy/SciPy 等二进制包含多种随附第三方许可；Psycopg 为 LGPL-3.0-only，certifi 为 MPL-2.0，tqdm 声明 MPL-2.0 AND MIT。它们并非由根目录 MIT 授权。当前仅分发项目源码与依赖清单，没有重打包这些二进制库。
- Streamlit 元数据声明 Apache-2.0，但当前安装元数据清单未列许可文件；可核对 [上游 LICENSE](https://github.com/streamlit/streamlit/blob/develop/LICENSE)。若以后分发安装包、镜像或离线依赖，需补核完整 LICENSE/NOTICE 与二进制附带条款。
- PostgreSQL 使用其 [PostgreSQL License](https://www.postgresql.org/about/licence/)；Docker Desktop 是本机外部工具，受 Docker 自身条款约束，不属于本项目 MIT 授权的代码。镜像与软件安装包未包含在拟发布清单中。
- 已搜索源码中的版权、引用来源及复制标记；没有据此推定所有无标记代码都完全原创。历史生成脚本、文档模板或未标注片段的完整来源链仍需作者确认；发现第三方片段时应保留其声明，不归入作者版权。
- Olist 数据、报告、截图和混合材料见 [数据许可](DATA_LICENSE.md)。将来商业使用、另行分发二进制/构建包或重授权前，应重新审查适用范围。
