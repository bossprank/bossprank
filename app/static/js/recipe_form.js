document.addEventListener('DOMContentLoaded', function () {
    const ingredientsContainer = document.getElementById('ingredients-container');
    const addIngredientBtn = document.getElementById('add-ingredient-btn');
    const recipeForm = document.getElementById('recipeForm');
    const ingredientRowTemplate = document.getElementById('ingredient-row-template');

    // Load data passed from template
    let allIngredients = [];
    try {
        allIngredients = JSON.parse(document.getElementById('all-ingredients-data').textContent);
    } catch (e) {
        console.error("Error parsing all_ingredients-data:", e);
        // Optionally, display an error to the user
    }

    let currentRecipeIngredients = [];
    try {
        currentRecipeIngredients = JSON.parse(document.getElementById('current-recipe-ingredients-data').textContent);
    } catch (e) {
        console.error("Error parsing current-recipe-ingredients-data:", e);
    }

    function createIngredientRowElement(ingredientData = null) {
        if (!ingredientRowTemplate) {
            console.error("Ingredient row template not found!");
            return null;
        }
        const templateClone = ingredientRowTemplate.content.cloneNode(true);
        const newRow = templateClone.querySelector('.ingredient-row');

        const selectEl = newRow.querySelector('.ingredient-select');
        const quantityEl = newRow.querySelector('.ingredient-quantity');
        const unitEl = newRow.querySelector('.ingredient-unit');

        // Populate dropdown with all ingredients
        allIngredients.forEach(ing => {
            const option = document.createElement('option');
            option.value = ing.id;
            option.textContent = ing.name;
            if (ingredientData && ing.id === ingredientData.ingredient_id) {
                option.selected = true;
            }
            selectEl.appendChild(option);
        });

        if (ingredientData) {
            quantityEl.value = ingredientData.quantity_used_in_recipe || '';
            unitEl.value = ingredientData.unit_used_in_recipe || '';
        }

        newRow.querySelector('.remove-ingredient-btn').addEventListener('click', () => {
            newRow.remove();
            updateFieldNames(); // Renumber fields when a row is removed
        });

        return newRow;
    }

    function addIngredientRowToContainer(ingredientData = null) {
        const newRowElement = createIngredientRowElement(ingredientData);
        if (newRowElement) {
            ingredientsContainer.appendChild(newRowElement);
            updateFieldNames(); // Renumber fields after adding a new row
        }
    }

    function updateFieldNames() {
        const rows = ingredientsContainer.querySelectorAll('.ingredient-row');
        rows.forEach((row, index) => {
            row.querySelector('.ingredient-select').name = `ingredient_id_${index}`;
            row.querySelector('.ingredient-quantity').name = `quantity_${index}`;
            row.querySelector('.ingredient-unit').name = `unit_${index}`;
        });
    }

    // Pre-populate with existing ingredients if editing
    if (currentRecipeIngredients && currentRecipeIngredients.length > 0) {
        currentRecipeIngredients.forEach(existingIngredient => {
            addIngredientRowToContainer(existingIngredient);
        });
    } else if (ingredientsContainer.children.length === 0) {
        // Add one empty row if creating a new recipe and no ingredients yet
        // addIngredientRowToContainer(); // Optionally add one by default
    }


    if (addIngredientBtn) {
        addIngredientBtn.addEventListener('click', () => addIngredientRowToContainer());
    }

    // Note: Form submission will use standard HTML form submission with numbered fields.
    // The backend will parse these `ingredient_id_X`, `quantity_X`, `unit_X` fields.
    // No special JavaScript is strictly needed for submission itself beyond this setup,
    // unless submitting as JSON, which would require more complex handling here.
});
