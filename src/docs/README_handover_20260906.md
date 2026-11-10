# 農田水利署綠能管考系統 — 開發交接文件

**交接時間**：2026-09-06
**專案負責人**：王文志（WWZ）· 台農院
**Firebase 專案 ID**：`william-858`
**填報頁面 URL**：https://william-858.web.app
**儀表板 GitHub**：https://github.com/William-858/green-energy-dashboard_histroy_PCM

---

## 一、系統架構總覽

兩個獨立部署的網頁：

```
┌─────────────────────────────────────┐
│  儀表板（唯讀展示 + 月報彙整）        │
│  → GitHub Pages                    │
│  → index.html = dashboard_editable_39.html │
└──────────────┬──────────────────────┘
               │ 匯入 Excel（人工）
               │
┌──────────────┴──────────────────────┐
│  管理處即時填報系統（14 處雙向填報） │
│  → Firebase Hosting                 │
│  → https://william-858.web.app      │
│  → Firestore: solar_sites 集合      │
└─────────────────────────────────────┘
```

## 二、資料流

1. **admin** 用「📥 匯入基底資料」把 filling_11508.html 的 snapshot JSON 一次性匯入 Firestore（solar_sites 集合）
2. **14 處管理處**登入填報頁面，看到自己管理處的案場清單，即時更新「案場進度」與「辦理情形」
3. 也可以透過「➕ 新增案場」新增（新處會覆蓋同 ID）、或「🗑️ 刪除」移除
4. **admin** 定期點「📤 匯出月報 Excel」，下載 ZIP（14 個管理處各一份 Excel，格式符合儀表板 importMonthlySubmissions 期望）
5. 解壓縮後在儀表板點**綠色**「📥 匯入即時填報」按鈕匯入所有 Excel
6. 儀表板案場階段/辦理情形隨之更新

## 三、Firebase 設定

**專案**：`william-858`
**Web App**：綠能管考（appId `1:71885072820:web:7e27d4fefb624aea812ae1`）

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyAl2-5duXzA5UnMLaTjYp4K2PBrnzZJ-EE",
  authDomain: "william-858.firebaseapp.com",
  projectId: "william-858",
  storageBucket: "william-858.firebasestorage.app",
  messagingSenderId: "71885072820",
  appId: "1:71885072820:web:7e27d4fefb624aea812ae1"
};
```

**已啟用服務**：
- Authentication（Email/Password）
- Firestore Database
- Hosting

**Firestore 安全規則**：目前寬鬆版（登入即可讀寫），試做期使用；未來需要收緊為「各處只能改自己管理處」

## 四、Firebase Authentication 帳號

**已建立**（3 組）：
- `admin@triwra.gov.tw` — 管理員（看全部、匯入基底、匯出月報 Excel）
- `taoyuan@triwra.gov.tw` — 桃園管理處
- `shimen@triwra.gov.tw` — 石門管理處

**尚未建立**（12 組，需手動在 Firebase Console → Authentication → Users 建）：
- `hsinchu@triwra.gov.tw` — 新竹
- `miaoli@triwra.gov.tw` — 苗栗
- `taichung@triwra.gov.tw` — 臺中
- `nantou@triwra.gov.tw` — 南投
- `changhua@triwra.gov.tw` — 彰化
- `yunlin@triwra.gov.tw` — 雲林
- `chianan@triwra.gov.tw` — 嘉南
- `kaohsiung@triwra.gov.tw` — 高雄
- `pingtung@triwra.gov.tw` — 屏東
- `yilan@triwra.gov.tw` — 宜蘭
- `hualien@triwra.gov.tw` — 花蓮
- `taitung@triwra.gov.tw` — 臺東

Email→管理處對應寫死在 `filling/index.html` 的 `EMAIL_TO_MGMT` 物件。

## 五、Firestore 資料結構

**Collection**: `solar_sites`
**Document ID 規則**: `{管理處}__{案場名稱}`（案場名稱替換掉 `/ . # $ [ ]` 為 `_`）

**Document 欄位**：
```typescript
{
  site_name: string,          // 案場名稱
  mgmt: string,               // 管理處（臺中/臺東 已 normalize）
  contract_name: string,      // 契約名稱
  vendor: string,             // 設置廠商
  capacity_mw: number,        // 裝置容量 MW
  site_count: number,         // 案場數量
  site_progress: string,      // 案場進度（舊資料才有）
  sign_date: string,          // 簽約日期
  install_deadline: string,   // 設置期限
  expire_status: string,      // 到期狀態
  current_stage: string,      // 案場進度（填報主欄位，10 個 stage 之一）
  current_operation: string,  // 辦理情形（填報主欄位）
  updated_at: Timestamp,      // 最後更新時間
  updated_by: string,         // 最後更新者（管理處名稱）
  updated_by_email: string,   // 最後更新者 email
  history: Array,             // 修改歷程
  manually_added?: boolean    // 是否為手動新增（非匯入）
}
```

**STAGE_OPTIONS**（10 個）：
`規劃中 / 尚未送件 / 土地容許 / 電業籌設 / 併聯審查(未送) / 併聯審查 / 施工階段 / 已併網 / 已解約 / 已撤案`

## 六、儀表板重要對應（SOLAR_STAGE_FILLING_MAP）

在 `dashboard_editable_39.html` line 1012 附近：

```javascript
const SOLAR_STAGE_FILLING_MAP = {
  '已併網': '已完工',
  '施工階段': '施工中',
  '已解約': '規劃中',    // ← 為維持 600.44 MW 總量，解約案退回規劃中
  '已撤案': '規劃中',    // ← 同上
  '土地容許': '申設中',
  '電業籌設': '申設中',
  '併聯審查': '申設中',
  '併聯審查(未送)': '規劃中',
  '尚未送件': '規劃中',
  '規劃中': '規劃中'
};
```

## 七、目前進度與已完成功能

**填報頁面**（filling/index.html, v4.1）：
- ✅ Email/密碼登入
- ✅ 各處只看自己管理處案場（admin 看全部 + mgmt 篩選器）
- ✅ 案場清單搜尋、階段篩選
- ✅ 編輯案場進度（下拉）+ 辦理情形（文字）→ 儲存到 Firestore
- ✅ 即時同步（onSnapshot）
- ✅ Admin 匯入基底資料（吃 filling_11508.html 的 snapshot JSON）
- ✅ Admin 匯出月報 Excel（14 檔 ZIP，格式符合儀表板 importMonthlySubmissions）
- ✅ 新增案場（14 處+admin 都可以）
- ✅ 刪除案場（各處只能刪自己的，admin 可刪任何）
- ✅ 撇除案場 ID 有括號時 querySelector 出錯的 bug（v4.1 修正）

**儀表板**（dashboard_editable_39.html）：
- ✅ 加了填報頁面連結 icon（桌面+手機 header）
- ✅ 加了「📥 匯入即時填報」按鈕連到 importMonthlySubmissions
- ✅ SOLAR_STAGE_FILLING_MAP 修正（已解約/已撤案 → 規劃中）
- ✅ 開場動畫（綠色漸層 + 進度條）
- ✅ 隱藏 3 個未完成按鈕（開新月報專案、匯出太陽光電/小水力 RiChi）

## 八、部署方式

### 填報頁面（Firebase Hosting）
1. Google Cloud Console → 右上 `>_` 開 Cloud Shell
2. 上傳 filling.zip
3. 執行：
   ```bash
   cd ~ && unzip -o filling.zip && cd filling && firebase deploy --only hosting
   ```
4. 首次要 `firebase login --no-localhost`

### 儀表板（GitHub Pages）
1. 進 GitHub repo `William-858/green-energy-dashboard_histroy_PCM`
2. 編輯 `index.html`
3. 全選刪除 → 貼上新版 → Commit

## 九、待辦事項（下一位接手可繼續）

1. **建 12 個管理處帳號**（Firebase Console → Authentication → Users）
2. **測試月報 Excel 匯入儀表板**：從填報頁面匯出 → GitHub 儀表板匯入 → 確認階段更新
3. **收緊 Firestore 安全規則**：試做穩定後，改為「各處只能改自己管理處」
4. **小水力（hydro）填報**：目前只做太陽光電。小水力有 3 種 sheet（hydro_tender / hydro_test / hydro_potential），架構可比照
5. **發信通知 14 處**：告知網址、帳號、密碼、使用方式

## 十、需要注意的技術細節

- 案場 ID 含特殊字元（如括號 `()`）時，CSS `querySelector` 會壞；請永遠用 `getElementById` + `.querySelector()`
- 「臺中/台中」「臺東/台東」在資料裡都有出現，`normMgmt()` 函式統一 normalize 為「臺」
- 填報頁面 Excel 匯出時，欄位名稱**必須用「目前階段」**（不是「案場進度」）—— 儀表板的 `_applySolarUpdate` 讀這個欄名
- Firebase Spark 免費方案對這個規模綽綽有餘

---

## 檔案清單

- `dashboard_editable_39.html` — 儀表板（放 GitHub 的 index.html）
- `filling/index.html` — 填報頁面主檔
- `filling/firebase.json` — Firebase Hosting 設定
- `filling/firestore.rules` — Firestore 安全規則
- `filling/.firebaserc` — 綁定專案 william-858

