/* global skillfarm, aaSkillfarmSettings, aaSkillfarmSettingsOverride, numberFormatter, _bootstrapTooltip */

$(document).ready(() => {

    $('.aa-skillfarm-editable').editable({
        container: 'body',
        type: 'number',
        title: 'Enter value',
        placement: 'top',
        /**
         * Disable display of the editable field value after editing
         */
        display: () => {
            return false;
        },
        success: function(response, newValue) {
            newValue = parseInt(newValue);

            const newValueFormatted = numberFormatter({
                value: newValue,
                locales: aaSkillfarmSettings.locale,
                options: {
                    style: 'currency',
                    currency: 'ISK'
                }
            });
            $(this).attr('data-value', newValue).html(newValueFormatted);
            calculate();
        },
        validate: (value) => {
            if (value === '') {
                return 'This field is required';
            } else if (isNaN(value) || parseFloat(value) < 0) {
                return 'Please enter a valid non-negative number';
            }
        }
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
    _bootstrapTooltip();
});
