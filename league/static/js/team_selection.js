document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submitBtn");
    const tier1DriverSelect = document.getElementById("id_tier_1_driver");
    const tier2DriverCheckboxes = document.querySelectorAll(".tier-2-driver");
    const budgetLimit = 20; // Budget in millions
    const raceForm = document.getElementById("raceForm");
    const maxDriversWarning = document.getElementById("max-drivers-warning");

    if (!raceForm) {
        console.error("Form element 'raceForm' not found!");
        return;
    }

    function calculateTotalCostAndValidateDrivers() {
        let totalCost = 0;
        let selectedTier2Count = 0;
        const selectedTier1Driver = tier1DriverSelect.selectedOptions[0]?.text;

        // Calculate cost of selected Tier 1 driver
        const tier1DriverPrice = tier1DriverSelect.selectedOptions[0]?.getAttribute("data-price");
        if (tier1DriverPrice) {
            totalCost += parseFloat(tier1DriverPrice);
        }

        // Calculate cost and count of selected Tier 2 drivers
        tier2DriverCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const driverPrice = checkbox.getAttribute("data-price");
                totalCost += parseFloat(driverPrice);
                selectedTier2Count++;
            }
        });

        // Determine maximum Tier 2 drivers allowed
        const maxTier2Drivers = selectedTier1Driver === "NA" ? 5 : 4;

        // Display warnings and disable submit button if conditions are not met
        if (selectedTier2Count > maxTier2Drivers) {
            maxDriversWarning.textContent = `You can select up to ${maxTier2Drivers} Tier 2 drivers.`;
            submitBtn.disabled = true;
        } else if (totalCost > budgetLimit) {
            maxDriversWarning.textContent = "Total cost exceeds $20M budget.";
            submitBtn.disabled = true;
        } else {
            maxDriversWarning.textContent = "";
            submitBtn.disabled = false;
        }
    }

    // Add event listeners to recalculate cost and validate on change
    tier1DriverSelect.addEventListener("change", calculateTotalCostAndValidateDrivers);
    tier2DriverCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", calculateTotalCostAndValidateDrivers);
    });

    // Initial calculation
    calculateTotalCostAndValidateDrivers();

    // Add submit event listener for Tier 2 driver validation
    raceForm.addEventListener("submit", function (event) {
        const selectedTier1Driver = tier1DriverSelect.selectedOptions[0]?.text;
        const isAnyTier2DriverSelected = Array.from(tier2DriverCheckboxes).some(cb => cb.checked);

        if (!isAnyTier2DriverSelected) {
            event.preventDefault();
            alert("You must select at least one Tier 2 driver before submitting your lineup.");
            return;
        }

        // Ensure no more than allowed Tier 2 drivers are selected
        const maxTier2Drivers = selectedTier1Driver === "NA" ? 5 : 4;
        const selectedTier2Count = Array.from(tier2DriverCheckboxes).filter(cb => cb.checked).length;

        if (selectedTier2Count > maxTier2Drivers) {
            event.preventDefault();
            alert(`You can select up to ${maxTier2Drivers} Tier 2 drivers.`);
        }
    });
});