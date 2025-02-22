/* global SkillfarmSettings, SkillFarmAjax */
$(document).ready(() => {
    const modalRequestSkillset = $('#skillfarm-skillset');

    // Store the original options in a variable
    const originalOptions = [...document.querySelectorAll('#skillSetSelect option')].map(option => ({
        value: option.value,
        text: option.textContent
    }));

    // Approve Request Modal
    modalRequestSkillset.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        let skillSetupURL = SkillfarmSettings.SkillSetupUrl;

        // Extract the character_id from the button
        const characterId = button.data('character-id');
        skillSetupURL = skillSetupURL.replace('12345', characterId);

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestSkillset.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestSkillset.find('#modal-request-text');
        modalDiv.html(modalText);

        // Set the character_id in the hidden input field
        modalRequestSkillset.find('input[name="character_id"]').val(characterId);

        // Fetch selected skills from the API and populate the selectedSkills list
        fetch(skillSetupURL)
            .then(response => {
                return response.json();
            })
            .then(data => {
                if (data.skillset && Array.isArray(data.skillset)) {
                    var selectedSkills = document.getElementById('selectedSkills');
                    selectedSkills.innerHTML = ''; // Clear existing selected skills
                    // Search for the option with the skill name and add it to the selected skills list
                    data.skillset.forEach(skill => {
                        var option = Array.from(document.querySelectorAll('#skillSetSelect option')).find(opt => opt.text === skill);
                        if (option) {
                            var li = document.createElement('li');
                            li.className = 'list-group-item d-flex justify-content-between align-items-center';
                            li.textContent = option.text;
                            li.dataset.skillId = option.value;

                            // Create a remove button for the list item
                            var removeButton = document.createElement('button');
                            removeButton.className = 'btn btn-danger btn-sm';
                            removeButton.textContent = 'Remove';
                            removeButton.addEventListener('click', function() {
                                option.selected = false;
                                li.remove();
                                document.getElementById('skillSetSelect').appendChild(option);
                            });

                            // Append the remove button to the list item
                            li.appendChild(removeButton);
                            // Add the skill to the selected skills list
                            selectedSkills.appendChild(li);
                            // Remove the option from the select list
                            option.remove();
                        } else {
                            console.warn(`Option with value "${skill}" not found.`);
                        }
                    });
                }
            })
            .catch(error => console.error('Error fetching selected skills:', error));

        // Confirm button click event
        $('#modal-button-confirm-skillset-request').on('click', () => {
            const form = modalRequestSkillset.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            // Remove any existing error messages
            form.find('.alert-danger').remove();

            // Get the selected skills
            const selectedSkills = [];
            $('#selectedSkills li').each(function() {
                const skillName = $(this).contents().filter(function() {
                    return this.nodeType === 3; // Node.TEXT_NODE
                }).text().trim();
                selectedSkills.push(skillName);
            });

            // Set the selected skills in the hidden input field
            form.find('input[name="selected_skills"]').val(selectedSkills.join(','));

            const posting = $.post(
                url,
                {
                    character_id: characterId,
                    csrfmiddlewaretoken: csrfMiddlewareToken,
                    selected_skills: selectedSkills.join(',')
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    // Reload the data after successful post
                    SkillFarmAjax.fetchDetails();

                    modalRequestSkillset.modal('hide');
                }
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        // Clear the modal content and reset input fields
        modalRequestSkillset.find('#modal-title').html('');
        modalRequestSkillset.find('#modal-request-text').html('');
        modalRequestSkillset.find('input[name="character_id"]').val('');
        modalRequestSkillset.find('input[name="selected_skills"]').val('');
        modalRequestSkillset.find('.alert-danger').remove();
        document.getElementById('selectedSkills').innerHTML = '';
        $('#modal-button-confirm-skillset-request').unbind('click');

        // Reset the search input and options
        var searchInput = document.getElementById('skillSearch');
        searchInput.value = '';

        // Reset the select options
        var skillSetSelect = document.getElementById('skillSetSelect');
        skillSetSelect.innerHTML = '';
        originalOptions.forEach(optionData => {
            var option = document.createElement('option');
            option.value = optionData.value;
            option.textContent = optionData.text;
            skillSetSelect.appendChild(option);
        });
    });

    // Search for skills in the select list
    document.getElementById('skillSearch').addEventListener('input', function() {
        var searchValue = this.value.toLowerCase();
        var options = document.getElementById('skillSetSelect').options;
        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            if (option.text.toLowerCase().includes(searchValue)) {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        }
    });

    // Add selected skills to the selected skills list
    document.getElementById('skillSetSelect').addEventListener('change', function() {
        var selectedSkills = document.getElementById('selectedSkills');
        var options = this.selectedOptions;
        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            if (!document.querySelector(`li[data-skill-id="${option.value}"]`)) {
                var li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.textContent = option.text;
                li.dataset.skillId = option.value;

                var removeButton = document.createElement('button');
                removeButton.className = 'btn btn-danger btn-sm';
                removeButton.textContent = 'Remove';
                removeButton.addEventListener('click', function() {
                    option.selected = false;
                    li.remove();
                    document.getElementById('skillSetSelect').appendChild(option);
                });

                li.appendChild(removeButton);
                selectedSkills.appendChild(li);
                option.remove();
            }
        }
    });
});
