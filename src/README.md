# 農田水利署綠能管考系統（原始碼包）

完整說明請看與本 zip 放在一起的 `AI交接包.md`；本輪開發過程請看 `開發對話紀錄.md`。

| 資料夾 | 內容 | 部署到 |
|---|---|---|
| `dashboard/` | 儀表板 `index.html`（＝目前 GitHub 上的版本）；`index_optional_stage_alias.html` 為選配版（多接受「已完工」等階段同義寫法），**不需部署** | GitHub repo `William-858/green-energy-dashboard_histroy_PCM` 的 `index.html` |
| `filling-firebase/` | 管理處即時填報系統（含 `.firebaserc` 隱藏檔） | Firebase Hosting，專案 `william-858`（https://william-858.web.app） |
| `data/` | 最新基底資料快照 `filling_11510_snapshot.html`（太陽光電 49 案，資料日期 2026-10-20） | 不上線；在填報頁「匯入基底資料」選檔 |
| `tools/` | `build_filling.py` ＋ 樣板：由 Excel 產生基底資料快照 | 本機執行 |
| `docs/` | 2026-09-06 的前一份交接文件 | — |

⚠️ `dashboard/index.html` 與 `filling-firebase/index.html` 檔名相同但內容完全不同，請勿搞混。
⚠️ 不要用 `data/` 的快照覆蓋 GitHub 上舊的 `filling.html`（那份含小水力資料）。
