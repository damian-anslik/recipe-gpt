from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser, SystemMessage, HumanMessage
from flask import Flask, request, jsonify
import dotenv
import json

dotenv.load_dotenv()
app = Flask(__name__)
chat_model = ChatOpenAI()


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


@app.route("/recipe", methods=["GET"])
def generate_recipe():
    prompt = request.args.get("prompt")
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
        result = chain.invoke({"text": prompt})
        return jsonify(result)
    except Exception:
        return (
            "An error occurred while generating the recipe. Please update the prompt and try again.",
            400,
        )


if __name__ == "__main__":
    app.run(
        port=8000,
    )
