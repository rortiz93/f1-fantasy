document.addEventListener("DOMContentLoaded", function() {
    const submitBtn = document.getElementById("submitBtn");
    const tier1DriverSelect = document.getElementById("id_tier_1_driver");
    const tier2DriverCheckboxes = document.querySelectorAll(".tier-2-driver");
    const budgetLimit = 20; // Budget in millions

    function calculateTotalCost() {
        let totalCost = 0;

        // Calculate cost of selected Tier 1 driver
        const tier1DriverPrice = tier1DriverSelect.selectedOptions[0]?.getAttribute("data-price");
        if (tier1DriverPrice) {
            totalCost += parseFloat(tier1DriverPrice);
        }

        // Calculate cost of selected Tier 2 drivers
        tier2DriverCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const driverPrice = checkbox.getAttribute("data-price");
                totalCost += parseFloat(driverPrice);
            }
        });

        // Disable submit button if over budget, enable if within budget
        if (totalCost > budgetLimit) {
            submitBtn.disabled = true;
            submitBtn.title = "Total cost exceeds $20M budget.";
        } else {
            submitBtn.disabled = false;
            submitBtn.title = "";
        }
    }

    // Add event listeners to recalculate cost on change
    tier1DriverSelect.addEventListener("change", calculateTotalCost);
    tier2DriverCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", calculateTotalCost);
    });

    // Initial calculation
    calculateTotalCost();
});