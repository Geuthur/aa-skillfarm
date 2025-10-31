/* global SkillfarmSettings, SkillFarmAjax, skillSelect */
$(document).ready(() => {
    const modalRequestSkillset = $('#skillfarm-skillset');

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
                if (data.setup && Array.isArray(data.setup.skillset)) {
                    skillSelect.setSelected(data.setup.skillset);
                }
            })
            .catch(error => {
                console.error('Error loading data:', error);
            });

        // Confirm button click event
        $('#modal-button-confirm-skillset-request').on('click', () => {
            const form = modalRequestSkillset.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();
            const SelectedSkills = JSON.stringify(skillSelect.getData());


            // Remove any existing error messages
            form.find('.alert-danger').remove();
            // Set the selected skills in the hidden input field
            form.find('input[name="selected_skills"]').val(SelectedSkills);

            const posting = $.post(
                url,
                {
                    character_id: characterId,
                    csrfmiddlewaretoken: csrfMiddlewareToken,
                    selected_skills: SelectedSkills
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
        $('#modal-button-confirm-skillset-request').unbind('click');
        skillSelect.setSelected([]);
    });
});
