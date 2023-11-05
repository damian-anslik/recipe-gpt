from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser, SystemMessage, HumanMessage
import streamlit as st
import tinydb
import json
import dotenv
import os

chat_model = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"])
recipes_db = tinydb.TinyDB("recipes.json", indent=4)
strings = {
    "PAGE_TITLE": "RecipeGPT",
    "PAGE_ICON": "🧑‍🍳",
    "SIDEBAR_TITLE": "RecipeGPT 🧑‍🍳",
    "TEXT_AREA_LABEL": "Enter a title or description for a dish and let RecipeGPT generate a recipe for you!",
    "TEXT_AREA_PLACEHOLDER": "Delicious and easy to make chicken curry",
    "GENERATE_BUTTON_LABEL": "Generate recipe",
    "RECIPE_BOOK_HEADER": "Recipe Book 📖",
    "WELCOME_HEADER": "Welcome to RecipeGPT 🧑‍🍳",
    "WELCOME_DESCRIPTION": "RecipeGPT is a recipe generation app powered by OpenAI's GPT-3 API. Simply enter a title or description for a dish in the sidebar and let RecipeGPT generate a recipe for you!",
    "WELCOME_FOOTER": "RecipeGPT is a powered by Langchain, OpenAI's GPT-3 API, and Streamlit.",
    "ERROR_MESSAGE": "Something went wrong. Please update your description and try again.",
    "INSTRUCTIONS_TAB_LABEL": "📃 Instructions",
    "INGREDIENTS_TAB_LABEL": "🛒 Ingredients",
    "EQUIPMENT_TAB_LABEL": "🫕 Required Equipment",
}


class RecipeOutputParser(BaseOutputParser):
    def is_valid_recipe(self, recipe_data):
        num_ingredients = len(recipe_data["ingredients"])
        num_required_equipment = len(recipe_data["equipment"])
        num_instructions = len(recipe_data["instructions"])
        return all(
            [
                num_ingredients > 0,
                num_required_equipment > 0,
                num_instructions > 0,
            ]
        )

    def parse(self, text):
        data_dict = json.loads(text)
        recipe_data = {
            "title": data_dict["title"],
            "ingredients": data_dict["ingredients"],
            "instructions": data_dict["instructions"],
            "equipment": data_dict["equipment"],
        }
        if not self.is_valid_recipe(recipe_data):
            raise Exception
        return recipe_data


def generate_recipe(prompt: str) -> dict[str, str | list[str]]:
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=f"""
                You are writing a digital recipe book for busy individuals. You should generate an appropriate recipe given a title or description of a dish.
                The recipes should be simple to follow, cheap to prepare, and the required ingredients should be easy to find in supermarkets.
                The generated recipe should include a title, a complete list of ingredients, preparation steps, and a list of the equipment needed to prepare that dish.
                In addition, you should follow the following guidelines when generating the recipe:
                
                0. (VERY IMPORTANT) The response should be formatted as a JSON document. The document should include the title, ingredients, instructions, and equipment as keys.
                1. Prefix any optional ingredients, instructions, or equipment with the string 'Optional:'. For example 'Optional: Garlic mincer' or 'Optional: Top with sour cream'.
                2. Ingredient list items should only contain the quantity and name of the ingredient. Do not include information about how an ingredient should be prepared, for example, instead of '500g chicken breast, sliced' you should write '500g chicken breast'.
                3. For ingredients that require preparation before they can be used, include the preparation steps as a separate step in the instructions section.
                4. List each ingredient or instruction, whether it is required or optional, on a separate line.
                5. Ensure that instructions are written in plain English, are easy to follow, and are complete sentences.
                6. Do not prefix any instructions steps with numbers. Simply describe the step.
                7. Use the metric system for all measurements, quantities, and temperatures. Do not use any other measurement systems.
                8. Do not say 'Enjoy!', 'Bon appetit!', or anything similar, at the end of the instructions.
                9. Generate an appropriate title for the recipe. The title should be a short, concise description of the dish. It does not need to be the same as the prompt.
                """
            ),
            HumanMessage(content=prompt),
        ]
    )
    chain = chat_prompt | chat_model | RecipeOutputParser()
    try:
        st.session_state["error"] = None
        recipe = chain.invoke({"text": prompt})
        recipes_db.insert(recipe)
        st.session_state["active_recipe"] = recipe
    except Exception:
        st.session_state["error"] = strings["ERROR_MESSAGE"]


def render_app():
    recipes = recipes_db.all()
    # State perists across app reruns, so even if the user deletes all recipes, the active recipe will still be set.
    if len(recipes) == 0 and st.session_state.get("active_recipe") is not None:
        st.session_state["active_recipe"] = None
    st.set_page_config(
        page_title=strings["PAGE_TITLE"],
        page_icon=strings["PAGE_ICON"],
    )
    with st.sidebar:
        with st.container():
            st.header(strings["SIDEBAR_TITLE"])
            prompt = st.text_area(
                label=strings["TEXT_AREA_LABEL"],
                placeholder=strings["TEXT_AREA_PLACEHOLDER"],
            )
            if error_message := st.session_state.get("error"):
                st.error(error_message)
            st.button(
                strings["GENERATE_BUTTON_LABEL"],
                on_click=lambda: generate_recipe(prompt),
                use_container_width=True,
                disabled=(prompt == ""),
            )
        with st.container():
            if len(recipes) != 0:
                st.header(strings["RECIPE_BOOK_HEADER"])
                for recipe in recipes:
                    st.button(
                        recipe["title"],
                        on_click=lambda recipe=recipe: st.session_state.update(
                            {"active_recipe": recipe}
                        ),
                        use_container_width=True,
                    )
    if st.session_state.get("active_recipe"):
        with st.container():
            st.header(st.session_state.get("active_recipe")["title"])
            instructions_tab, ingredients_tab, equipment_tab = st.tabs(
                [
                    strings["INSTRUCTIONS_TAB_LABEL"],
                    strings["INGREDIENTS_TAB_LABEL"],
                    strings["EQUIPMENT_TAB_LABEL"],
                ]
            )
            with instructions_tab:
                for step_num, instruction in enumerate(
                    st.session_state.get("active_recipe")["instructions"], start=1
                ):
                    st.markdown(f"{step_num}. {instruction}")
            with ingredients_tab:
                for ingredient in st.session_state.get("active_recipe")["ingredients"]:
                    st.markdown(f"- {ingredient}")
            with equipment_tab:
                for item in st.session_state.get("active_recipe")["equipment"]:
                    st.markdown(f"- {item}")
    else:
        with st.container():
            st.header(strings["WELCOME_HEADER"])
            st.markdown(strings["WELCOME_DESCRIPTION"])
            st.markdown(strings["WELCOME_FOOTER"])


if __name__ == "__main__":
    dotenv.load_dotenv()
    render_app()
