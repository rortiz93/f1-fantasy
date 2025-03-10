document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submitBtn");
    const useMulliganBtn = document.getElementById("useMulliganBtn");
    const useOverdriveBtn = document.getElementById("useOverdriveBtn");
    const tier1DriverSelect = document.getElementById("id_tier_1_driver");
    const tier2DriverCheckboxes = document.querySelectorAll(".tier-2-driver");
    const budgetLimit = 50; // Budget in millions
    const raceForm = document.getElementById("raceForm");
    const maxDriversWarning = document.getElementById("max-drivers-warning");
    const container = document.getElementById("mulligan-container");
    const leagueId = container.getAttribute("data-league-id");
    const teamId = container.getAttribute("data-team-id");

    const infoIcon = document.getElementById("infoIcon");
    const infoPopup = document.getElementById("infoPopup");
    const closeInfoPopup = document.getElementById("closeInfoPopup");

    infoIcon.addEventListener("click", function () {
        infoPopup.style.display = "block";
    });

    closeInfoPopup.addEventListener("click", function () {
        infoPopup.style.display = "none";
    });

    // Optional: close the popup when clicking outside of it
    document.addEventListener("click", function (event) {
        if (!infoPopup.contains(event.target) && !infoIcon.contains(event.target)) {
            infoPopup.style.display = "none";
        }
    });
    
    function updateSubmitButtonState() {
        console.log("Current time:", new Date());
        console.log("isAfterLineupDeadline:", isAfterLineupDeadline);
        console.log("isBeforeMulliganDeadline:", isBeforeMulliganDeadline);
        if (isAfterLineupDeadline && !isBeforeMulliganDeadline) {
            // After lineup deadline and mulligan window is closed: disable submit button
            submitBtn.disabled = true;
        } else if (isAfterLineupDeadline && isBeforeMulliganDeadline) {
            // After lineup deadline but before mulligan deadline: keep submit disabled until mulligan is used
            submitBtn.disabled = true;
        } else {
            // Before lineup deadline: normal validation applies
            submitBtn.disabled = false;
            calculateTotalCostAndValidateDrivers();
        }
    }
    // Use these variables in your fetch call
    const url = `/league/${leagueId}/team/${teamId}/activate-mulligan/`;
    function handleMulliganActivation() {
        fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": "{{ csrf_token }}",
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Indicate that a mulligan is active
                submitBtn.disabled = false; 
                const messageDiv = document.getElementById("mulliganMessage");
                messageDiv.textContent = "Mulligan in Use - Adjust your lineup before the deadline.";
                messageDiv.classList.add("alert", "alert-info");
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error("Error activating mulligan:", error);
            alert("Failed to activate mulligan. Please try again.");
        });
    }

    if (useMulliganBtn) {
        useMulliganBtn.addEventListener("click", handleMulliganActivation);
    }
  

    if (useOverdriveBtn) {
        useOverdriveBtn.addEventListener("click", function () {
            fetch(`/league/${leagueId}/team/${teamId}/activate-overdrive/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                overdriveMessage.textContent = data.message;
                if (data.status === "success") {
                    // Show the additional interface for selecting a driver
                          // Generate a dropdown (example)
                    const overdriveSelect = document.getElementById("overdriveDriverSelect");
                    overdriveSelect.innerHTML = ""; // Clear existing options
                    tier2DriverCheckboxes.forEach(checkbox => {
                        if (checkbox.checked) {
                            const option = document.createElement("option");
                            option.value = checkbox.value;
                            option.textContent = checkbox.nextSibling.innerHTML; // Driver name
                            overdriveSelect.appendChild(option);
                        }
                    });
                    const overdriveRow = document.getElementById("overdrive-driver-container");
                    overdriveRow.style.display = "block";
                }
            })
            .catch(error => {
                console.error("Error activating overdrive:", error);
                overdriveMessage.textContent = "Failed to activate overdrive. Please try again.";
            });
        });
    }


    // Show the dropdown
    //document.getElementById("overdrive-driver-container").style.display = "block";

    const confirmOverdriveDriverBtn = document.getElementById("confirmOverdriveDriverBtn");
    if (confirmOverdriveDriverBtn) {
        confirmOverdriveDriverBtn.addEventListener("click", function () {
            const driverId = overdriveSelect.value;
            if (!driverId) {
                overdriveDriverMessage.textContent = "Please select a Tier 2 driver.";
                return;
            }

            fetch(`/league/${leagueId}/team/${teamId}/set-overdrive-driver/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ driver_id: driverId })
            })
            .then(response => response.json())
            .then(data => {
                overdriveDriverMessage.textContent = data.message;
                if (data.status === "success") {
                    // Provide feedback or close the dropdown, if desired
                }
            })
            .catch(error => {
                console.error("Error setting overdrive driver:", error);
                overdriveDriverMessage.textContent = "Failed to set overdrive driver. Please try again.";
            });
        });
    }
    updateSubmitButtonState();

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
        const maxTier2Drivers = selectedTier1Driver === "NA - $0M" ? 5 : 4;

        // Display warnings and disable submit button if conditions are not met
        if (selectedTier2Count > maxTier2Drivers) {
            maxDriversWarning.textContent = `You can select up to ${maxTier2Drivers} Tier 2 drivers.`;
            //submitBtn.disabled = true;
        } else if (totalCost > budgetLimit) {
            maxDriversWarning.textContent = "Total cost exceeds $50M budget.";
            //submitBtn.disabled = true;
        } else {
            maxDriversWarning.textContent = "";

            //submitBtn.disabled = false;
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
        const maxTier2Drivers = selectedTier1Driver === "NA - $0M" ? 5 : 4;
        const selectedTier2Count = Array.from(tier2DriverCheckboxes).filter(cb => cb.checked).length;

        if (selectedTier2Count > maxTier2Drivers) {
            event.preventDefault();
            alert(`You can select up to ${maxTier2Drivers} Tier 2 drivers.`);
        }
    });
});