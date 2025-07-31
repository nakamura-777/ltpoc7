
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("資金寿命 × キャッシュ生産性：トレンド & 感度分析ツール")

# --- 1. 月次現金残高履歴入力 ---
st.header("📅 1. 月別現金残高の履歴入力")

monthly_data = st.data_editor(
    pd.DataFrame({
        "月": ["2024-01", "2024-02", "2024-03"],
        "期首現金残高（万円）": [1000, 800, 700],
        "期末現金残高（万円）": [800, 700, 650]
    }),
    num_rows="dynamic",
    use_container_width=True
)

# --- 2. 製品別 TP / LT 入力 ---
st.header("📦 2. 製品別 TP / LT 入力")

product_data = st.data_editor(
    pd.DataFrame({
        "製品名": ["製品A", "製品B"],
        "TP（万円）": [500, 1000],
        "LT（日）": [30, 60]
    }),
    num_rows="dynamic",
    use_container_width=True
)

# --- 加重平均計算 ---
valid_products = product_data.dropna()
total_tp = valid_products["TP（万円）"].sum()
weighted_lt = (valid_products["TP（万円）"] * valid_products["LT（日）"]).sum() / total_tp if total_tp > 0 else 0
cash_productivity = total_tp / weighted_lt if weighted_lt > 0 else 0
monthly_tp = cash_productivity * 30

# --- 3. 資金トレンド分析 ---
st.header("📈 3. 資金トレンド分析")

trend_df = monthly_data.copy()
trend_df["月間支出"] = trend_df["期首現金残高（万円）"] - trend_df["期末現金残高（万円）"]
trend_df["月間キャッシュ創出（TP起点）"] = monthly_tp
trend_df["月間純収支"] = trend_df["月間キャッシュ創出（TP起点）"] - trend_df["月間支出"]
trend_df["翌月想定残高"] = trend_df["期末現金残高（万円）"] + trend_df["月間純収支"]

st.dataframe(trend_df, use_container_width=True)

fig, ax = plt.subplots()
ax.plot(trend_df["月"], trend_df["期末現金残高（万円）"], marker='o', label="実績")
ax.plot(trend_df["月"], trend_df["翌月想定残高"], marker='x', linestyle='--', label="翌月予測")
ax.axhline(0, color='red', linestyle='--', label="資金枯渇ライン")
ax.set_xlabel("月")
ax.set_ylabel("現金残高（万円）")
ax.set_title("月別資金残高トレンド")
ax.legend()
st.pyplot(fig)

# --- 4. 感度分析 ---
st.header("🔍 4. 感度分析シミュレーション")

col1, col2, col3 = st.columns(3)
with col1:
    tp_rate = st.slider("TP 改善率（%）", -50, 100, 0)
with col2:
    lt_rate = st.slider("LT 短縮率（%）", -50, 50, 0)
with col3:
    cash_injection = st.number_input("現金注入額（万円）", min_value=0.0, value=0.0)

improved_tp = total_tp * (1 + tp_rate / 100)
improved_lt = weighted_lt * (1 - lt_rate / 100)
improved_productivity = improved_tp / improved_lt if improved_lt > 0 else 0
improved_monthly_tp = improved_productivity * 30
latest_cash = trend_df["期末現金残高（万円）"].iloc[-1] + cash_injection
latest_outflow = trend_df["月間支出"].iloc[-1]
net_change = improved_monthly_tp - latest_outflow

if net_change < 0:
    survival_months = latest_cash / abs(net_change)
    survival_msg = f"⚠ 資金注入後もあと {survival_months:.2f} ヶ月で枯渇"
elif net_change == 0:
    survival_msg = "🟡 トントン運営、維持可能"
else:
    survival_msg = "🟢 黒字化、資金は増加傾向"

st.markdown(f"""
**改善後TP**：{improved_tp:.1f} 万円  
**改善後LT**：{improved_lt:.1f} 日  
**改善後生産性（TP/LT）**：{improved_productivity:.2f} 万円／日  
**月間純収支**：{net_change:.2f} 万円  
**資金寿命（見込）**：{survival_msg}
""")

# --- 5. Excel出力 ---
st.header("📤 5. Excel ダウンロード")

def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet)
    return output.getvalue()

excel_binary = to_excel({
    "月別履歴": trend_df,
    "製品別TP_LT": product_data
})

st.download_button(
    label="📥 Excel出力：資金寿命分析.xlsx",
    data=excel_binary,
    file_name="資金寿命分析.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
