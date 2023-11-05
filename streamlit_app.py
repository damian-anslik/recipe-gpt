import streamlit as st
import requests

st.set_page_config(
    page_title="RecipeGPT",
    page_icon="🧑‍🍳",
)

# Page layout
st.title("RecipeGPT 🧑‍🍳")

# Inputs - Prompt and measurement system
prompt = st.text_area(
    "Enter a title or description of a dish:",
    value="Chicken and vegetable stir fry",
)

# Handle button click and render recipe
if st.button("Generate recipe"):
    recipe_response = requests.get(
        "http://localhost:8000/recipe",
        params={"prompt": prompt, "use_metric": True},
    )
    if not recipe_response.ok:
        st.error(
            "Something went wrong. Please update the dish description and try again."
        )
        st.stop()
    recipe_data = recipe_response.json()
    title = recipe_data["title"]
    ingredients = recipe_data["ingredients"]
    instructions = recipe_data["instructions"]
    equipment = recipe_data["equipment"]

    # Display the recipe in two grids
    with st.container():
        st.header(title)
        instructions_tab, ingredients_tab, equipment_tab = st.tabs(
            ["Instructions 📃", "Ingredients 🛒", "Required Equipment 🫕"]
        )
        with instructions_tab:
            for step_num, instruction in enumerate(instructions, start=1):
                st.markdown(f"{step_num}. {instruction}")
        with ingredients_tab:
            for ingredient in ingredients:
                st.markdown(f"- {ingredient}")
        with equipment_tab:
            for item in equipment:
                st.markdown(f"- {item}")
