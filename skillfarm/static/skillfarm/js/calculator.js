/* global skillfarm */

$(document).ready(() => {
    $('.editable-click').editable({
        type: 'number',
        title: 'Enter value',
        placement: 'top',
        display: function(value) {
            // Display the value with thousands separators
            if (!value) {
                // Display the original value if the new value is empty
                value = $(this).data('original');
            } else {
                // Store the new value
                $(this).text(parseFloat(value).toLocaleString());
            }
        },
        success: function(response, newValue) {
            // Check if the new value is empty
            if (!newValue) {
                console.log('Empty value');
                // Revert to the original value
                const originalValue = $(this).data('original');
                $(this).text(parseFloat(originalValue).toLocaleString());
            } else {
                // Display the value with thousands separators after saving
                $(this).text(parseFloat(newValue).toLocaleString());
            }
            calculate();
        },
        inputclass: 'editable-input',
        onblur: 'submit'
    });

    // Remove thousands separators when the input field is shown
    $('.editable-click').on('shown', function(e, editable) {
        var value = $(this).text().replace(/[,.]/g, '');
        editable.input.$input.val(value);
    });

    const elements = ['duration', 'injector-amount', 'extractor-amount', 'custom-plex-amount'];
    elements.forEach(id => {
        document.getElementById(id).addEventListener('change', calculate);
        document.getElementById(id).addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                calculate();
            }
        });
    });

    document.getElementById('calculator-form').addEventListener('submit', function(event) {
        event.preventDefault();
        calculate();
    });

    document.getElementById('custom-plex-checkbox').addEventListener('change', function() {
        const customPlexAmountContainer = document.getElementById('custom-plex-amount-container');
        const durationSelect = document.getElementById('duration');
        if (this.checked) {
            customPlexAmountContainer.style.display = 'block';
            durationSelect.disabled = true;
        } else {
            customPlexAmountContainer.style.display = 'none';
            durationSelect.disabled = false;
        }
        calculate();
    });

    // Add event listener for the calculate button
    document.getElementById('calculate').addEventListener('click', function() {
        calculate();
    });

    function calculate() {
        const injectorAmount = parseFloat(document.getElementById('injector-amount').value) || 0;
        const extraktorAmount = parseFloat(document.getElementById('extractor-amount').value) || 0;
        const duration = parseInt(document.getElementById('duration').value);
        const useCustomPlex = document.getElementById('custom-plex-checkbox').checked;
        const customPlexAmount = parseFloat(document.getElementById('custom-plex-amount').value) || 0;

        if (injectorAmount === 0 && extraktorAmount === 0) {
            document.getElementById('error').classList.remove('d-none');
            document.getElementById('result-text').classList.add('d-none');
            document.getElementById('result').innerHTML = '';
            return;
        }

        // Get the prices from the editable fields or use the original values
        const injectorPrice = parseFloat(document.getElementById('injektor').innerText.replace(/[,.]/g, '')) || parseFloat(skillfarm.injektor.average_price);
        const extraktorPrice = parseFloat(document.getElementById('extratkor').innerText.replace(/[,.]/g, '')) || parseFloat(skillfarm.extratkor.average_price);
        const plexPrice = parseFloat(document.getElementById('plex').innerText.replace(/[,.]/g, '')) || parseFloat(skillfarm.plex.average_price);

        const totalInjectorPrice = (injectorPrice * injectorAmount) - (extraktorPrice * extraktorAmount);

        let plexMultiplier;
        if (useCustomPlex) {
            plexMultiplier = customPlexAmount;
        } else {
            if (duration === 1) {
                plexMultiplier = 500;
            } else if (duration === 12) {
                plexMultiplier = 300;
            } else if (duration === 24) {
                plexMultiplier = 275;
            }
        }
        const totalPlexPrice = plexPrice * plexMultiplier;
        const totalPrice = totalInjectorPrice - totalPlexPrice;

        let resultText;
        resultText = `<span style="color: ${totalPrice < 0 ? 'red' : 'green'};">${Math.round(totalPrice).toLocaleString()} ISK</span>`;

        document.getElementById('result').innerHTML = resultText;
        document.getElementById('error').classList.add('d-none');
        document.getElementById('result-text').classList.remove('d-none');
    }

    $('[data-tooltip-toggle="skillfarm-tooltip"]').tooltip({
        trigger: 'hover',
    });
});
