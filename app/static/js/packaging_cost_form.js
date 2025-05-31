document.addEventListener('DOMContentLoaded', function () {
    const recipeIdSelect = document.getElementById('recipe_id');
    const unitsPerBatchContainer = document.getElementById('units_per_batch_container');
    const unitsPerBatchInput = document.getElementById('units_per_recipe_batch');

    function toggleUnitsPerBatchVisibility() {
        if (!recipeIdSelect || !unitsPerBatchContainer || !unitsPerBatchInput) {
            // If elements are not found (e.g. different form), do nothing.
            return;
        }

        if (recipeIdSelect.value && recipeIdSelect.value !== "") {
            // A recipe is selected
            unitsPerBatchContainer.style.display = ''; // Show
            unitsPerBatchInput.required = true;
        } else {
            // No recipe selected ("None" option)
            unitsPerBatchContainer.style.display = 'none'; // Hide
            unitsPerBatchInput.required = false;
            // unitsPerBatchInput.value = ''; // Optionally clear the value
        }
    }

    if (recipeIdSelect) {
        // Initial check on page load
        toggleUnitsPerBatchVisibility();

        // Add event listener for changes
        recipeIdSelect.addEventListener('change', toggleUnitsPerBatchVisibility);
    }

    // Handle form submission validation for units_per_recipe_batch
    const form = document.getElementById('packagingCostForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (recipeIdSelect && recipeIdSelect.value && recipeIdSelect.value !== "") {
                if (!unitsPerBatchInput.value || parseFloat(unitsPerBatchInput.value) <= 0) {
                    // alert('Please provide a valid positive number for "Units per Recipe Batch" when a recipe is selected.');
                    // Instead of alert, rely on HTML5 'required' validation or add custom feedback
                    if (!unitsPerBatchInput.checkValidity()) {
                         // Browser will show default validation message for required or type mismatch
                        unitsPerBatchInput.reportValidity(); // Trigger browser validation UI
                        event.preventDefault(); // Stop form submission
                    }
                }
            }
        });
    }
});
