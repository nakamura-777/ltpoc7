
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

# --- 各製品の TP/LT を平均 ---
valid_products = product_data.dropna()
valid_products["TP_per_LT"] = valid_products["TP（万円）"] / valid_products["LT（日）"]
cash_productivity = valid_products["TP_per_LT"].mean() if not valid_products.empty else 0
total_tp = valid_products["TP（万円）"].sum()
daily_tp_from_total = total_tp / 30 if total_tp > 0 else 0
monthly_tp = cash_productivity * 30

# --- 3. 資金トレンド分析 ---
st.header("📈 3. 資金トレンド分析")

trend_df = monthly_data.copy()
trend_df["月間収支"] = trend_df["期末現金残高（万円）"] - trend_df["期首現金残高（万円）"]

st.dataframe(trend_df, use_container_width=True)

fig, ax = plt.subplots()
ax.plot(trend_df["月"], trend_df["期末現金残高（万円）"], marker='o', label="期末残高（実績）")
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

# 改善後計算
improved_products = valid_products.copy()
improved_products["TP（万円）"] *= (1 + tp_rate / 100)
improved_products["LT（日）"] *= (1 - lt_rate / 100)
improved_products["TP_per_LT"] = improved_products["TP（万円）"] / improved_products["LT（日）"]
improved_productivity = improved_products["TP_per_LT"].mean() if not improved_products.empty else 0
improved_monthly_tp = improved_productivity * 30

latest_cash = trend_df["期末現金残高（万円）"].iloc[-1] + cash_injection
latest_outflow = -trend_df["月間収支"].iloc[-1]
net_change = improved_monthly_tp - latest_outflow

if net_change < 0:
    survival_months = latest_cash / abs(net_change)
    survival_msg = f"⚠ 資金注入後もあと {survival_months:.2f} ヶ月で枯渇"
elif net_change == 0:
    survival_msg = "🟡 トントン運営、維持可能"
else:
    survival_msg = "🟢 黒字化、資金は増加傾向"

st.dataframe(valid_products, use_container_width=True)

st.markdown(f"""\n**製品別 TP/LT（万円/日）** を表に表示\n\n**TP 合計**：{total_tp:.2f} 万円\n**TP 合計からの1日あたり TP**：{daily_tp_from_total:.2f} 万円/日\n
**平均キャッシュ生産性（TP/LT）**：{cash_productivity:.2f} 万円／日  
**改善後生産性**：{improved_productivity:.2f} 万円／日  
**月間純収支（改善後）**：{net_change:.2f} 万円  
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
    "製品別TP_LT": valid_products
})

st.download_button(
    label="📥 Excel出力：資金寿命分析.xlsx",
    data=excel_binary,
    file_name="資金寿命分析.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
