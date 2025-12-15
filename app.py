import streamlit as st
import pandas as pd
import joblib
import numpy as np


st.set_page_config(
    page_title="Smart Culinary Predictor",
    page_icon="🍽",
    layout="centered"
)


@st.cache_resource
def load_resources():
    dataset = pd.read_csv("Smart_Culinary_Training_Data.csv")
    model = joblib.load("rf_model.joblib")
    encoder = joblib.load("encoder.joblib")
    model_columns = joblib.load("model_columns.joblib")
    return dataset, model, encoder, model_columns

try:
    dataset, model, encoder, model_columns = load_resources()
except Exception as e:
    st.error(f"Error loading resources: {e}")
    st.stop()


st.title("🍽 Smart Culinary Calorie Predictor")
st.markdown("Calculate final calories based on **Food**, **Portion Size**, **Added Fat**, and **Cooking Method**.")
st.markdown("---")

input_mode = st.radio(
    "How would you like to enter data?",
    ["Select from Food List", "Enter Custom Manual Data"],
    horizontal=True
)

st.markdown("---")


col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Food Details")

    if input_mode == "Select from Food List":
        food_name = st.selectbox("Select Food Item", sorted(dataset["Food_Name"].unique()))

        ref_row = dataset[dataset["Food_Name"] == food_name].iloc[0]
        base_ref_weight = float(ref_row["Raw_Weight_g"])
        base_ref_cal = float(ref_row["Raw_Calories"])
        base_ref_fat = float(ref_row["Raw_Fat_g"])
        base_cat_id = ref_row["Category_ID"]

        user_weight = st.number_input("Raw Weight (g)", min_value=1.0, value=base_ref_weight, step=10.0, format="%.2f")

        scale_factor = user_weight / base_ref_weight if base_ref_weight > 0 else 1.0

        final_input_calories = base_ref_cal * scale_factor
        final_input_fat = base_ref_fat * scale_factor

        st.info(f"📊 Auto-Calculated Base Content:\n\n**{final_input_calories:.0f} kcal** | **{final_input_fat:.1f}g fat**")

    else:

        user_weight = st.number_input("Raw Weight (g)", min_value=1.0, value=100.0, step=10.0)
        final_input_calories = st.number_input("Total Raw Calories (kcal)", min_value=0.0, value=100.0, step=10.0)
        final_input_fat = st.number_input("Total Raw Fat (g)", min_value=0.0, value=0.0, step=1.0)


        base_cat_id = 11

with col2:
    st.subheader("2. Cooking Details")

    cooking_method = st.selectbox("Cooking Method", encoder.categories_[0])

    fat_added_tbsp = st.number_input("Fat Added (tbsp)", min_value=0.0, value=0.0, step=0.5, format="%.2f")


if st.button("🔥 Predict Final Calories", type="primary"):
    try:

        estimated_final_weight = user_weight * 0.9

        encoded_matrix = encoder.transform([[cooking_method]])
        encoded_df = pd.DataFrame(encoded_matrix, columns=encoder.get_feature_names_out(['Cooking_Method']))


        input_dict = {
            "Category_ID": base_cat_id,
            "Raw_Calories": final_input_calories,
            "Raw_Fat_g": final_input_fat,
            "Raw_Weight_g": user_weight,
            "Fat_Added_tbsp": 0.0,
            "Target_Final_Weight_g": estimated_final_weight
        }

        full_input = pd.concat([pd.DataFrame([input_dict]), encoded_df], axis=1)

        full_input = full_input.reindex(columns=model_columns, fill_value=0)

        base_prediction = model.predict(full_input)[0]

        fat_calories_math = fat_added_tbsp * 120.0

        final_prediction = base_prediction + fat_calories_math


        st.success(f"### Estimated Final Calories: {final_prediction:,.0f} kcal")

        with st.expander("ℹ️  See Calculation Breakdown"):
            st.write("Calculation Logic:")
            c1, c2, c3 = st.columns(3)
            c1.metric("Base Raw Calories", f"{final_input_calories:.0f}")
            c2.metric("Fat Added (Manual)", f"+{fat_calories_math:.0f} kcal")
            c3.metric("Predicted Total", f"{final_prediction:.0f} kcal")

    except Exception as e:
        st.error(f"Prediction Error: {e}")
