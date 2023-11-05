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
    st.session_state["error"] = False
    chain = chat_prompt | chat_model | RecipeOutputParser()
    try:
        recipe = chain.invoke({"text": prompt})
        recipes_db.insert(recipe)
        render_recipe_details(recipe)
    except Exception:
        st.session_state["error"] = True


def create_app():
    st.set_page_config(
        page_title="RecipeGPT",
        page_icon="🧑‍🍳",
    )
    if st.session_state.get("is_loading") is None:
        recipes = recipes_db.all()
        if len(recipes) != 0:
            render_recipe_details(recipes[-1])
            st.session_state["is_loading"] = False


def render_sidebar():
    with st.sidebar:
        st.title("RecipeGPT 🧑‍🍳")
        prompt = st.text_area(
            label="Enter a title or description for a dish and let RecipeGPT generate a recipe for you!",
            placeholder="Delicious and easy to make chicken curry",
        )
        if st.session_state.get("error"):
            st.error(
                "Something went wrong. Please update your description and try again."
            )
        st.button(
            "Generate recipe",
            on_click=lambda: generate_recipe(prompt),
            use_container_width=True,
        )
        if recipes := recipes_db.all():
            st.header("Recipe Book 📖")
            for recipe in recipes:
                st.button(
                    recipe["title"],
                    on_click=lambda recipe=recipe: render_recipe_details(recipe),
                    use_container_width=True,
                )


def render_recipe_details(recipe: dict[str, str | list[str]]):
    st.header(recipe["title"])
    instructions_tab, ingredients_tab, equipment_tab = st.tabs(
        ["📃 Instructions", "🛒 Ingredients", "🫕 Required Equipment"]
    )
    with instructions_tab:
        for step_num, instruction in enumerate(recipe["instructions"], start=1):
            st.markdown(f"{step_num}. {instruction}")
    with ingredients_tab:
        for ingredient in recipe["ingredients"]:
            st.markdown(f"- {ingredient}")
    with equipment_tab:
        for item in recipe["equipment"]:
            st.markdown(f"- {item}")


def main():
    create_app()
    render_sidebar()


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()
