$(document).ready(() => {
    /* global SkillFarmAjax */
    const modalRequestApprove = $('#skillfarm-confirm');



    // Approve Request Modal
    modalRequestApprove.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestApprove.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestApprove.find('#modal-request-text');
        modalDiv.html(modalText);

        // Set the character_id in the hidden input field
        const characterId = button.data('character-id');
        modalRequestApprove.find('input[name="character_id"]').val(characterId);

        $('#modal-button-confirm-confirm-request').on('click', () => {
            const form = modalRequestApprove.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            // Remove any existing error messages
            form.find('.alert-danger').remove();

            const posting = $.post(
                url,
                {
                    character_id: characterId,
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    // Reload the data after successful post
                    SkillFarmAjax.fetchDetails();

                    modalRequestApprove.modal('hide');
                }
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestApprove.find('.alert-danger').remove();
        $('#modal-button-confirm-confirm-request').unbind('click');
    });
});
