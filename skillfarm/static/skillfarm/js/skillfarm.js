/* global skillfarmSettings */
/* global bootstrap */

document.addEventListener('DOMContentLoaded', function() {
    var csrfToken = skillfarmSettings.csrfToken;
    var urlAlarm = skillfarmSettings.switchAlarmUrl;
    var urlSkillset = skillfarmSettings.switchSkillSetpUrl;
    var urlDeleteChar = skillfarmSettings.deleteCharUrl;
    var url = skillfarmSettings.skillfarmUrl;
    var characterPk = skillfarmSettings.characterPk;
    // Translations
    var switchAlarmText = skillfarmSettings.switchAlarmConfirmText;
    var switchAlarm = skillfarmSettings.switchAlarmText;
    var switchSkillset = skillfarmSettings.switchSkillsetText;
    var deleteChar = skillfarmSettings.deleteCharText;
    var deleteCharConfirm = skillfarmSettings.deleteCharConfirmText;
    var alarmActivated = skillfarmSettings.alarmActivatedText;
    var alarmDeactivated = skillfarmSettings.alarmDeactivatedText;
    var notupdated = skillfarmSettings.notUpdatedText;
    var noActiveTraining = skillfarmSettings.noActiveTrainingText;

    function switchAlarmUrl(characterId) {
        return urlAlarm
            .replace('1337', characterId);
    }

    function switchSkillSetpUrl(characterId) {
        return urlSkillset
            .replace('1337', characterId);
    }

    function deleteCharUrl(characterId) {
        return urlDeleteChar
            .replace('1337', characterId);
    }

    var confirmModal = document.getElementById('confirmModal');
    var confirmRequest = document.getElementById('confirm-request');
    var finalizeActionButton = document.getElementById('finalizeActionButton');

    confirmModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var confirmText = button.getAttribute('data-confirm-text');
        var formId = button.getAttribute('data-form-id');

        confirmRequest.textContent = confirmText;

        finalizeActionButton.onclick = function () {
            document.getElementById(formId).submit();
            var modal = bootstrap.Modal.getInstance(confirmModal);
            modal.hide();
        };
    });

    // Initialize DataTable
    var table = $('#skillfarm-details').DataTable({
        order: [[0, 'asc']],
        pageLength: 50,
        columnDefs: [
            { 'orderable': false, 'targets': 'no-sort' }
        ],
        createdRow: function(row, data, dataIndex) {
            $('td:eq(5)', row).addClass('text-end');
        }
    });

    function totalProgressbar (skillqueue) {
        var skillJson = JSON.parse(skillqueue);
        var totalSP = 0;
        var trainedSP = 0;

        skillJson.forEach(skill => {
            totalSP += skill.end_sp;
            trainedSP += skill.trained_sp;
        });

        var progressPercent = (trainedSP / totalSP) * 100;

        return progressPercent;
    }

    function calculateSumProgressBar(skillqueue, skills) {
        var skillqueueJson = JSON.parse(skillqueue);
        var skillsJson = JSON.parse(skills);

        // If there are no skills, return the total progress bar
        if (skillsJson.length === 0) {
            return totalProgressbar(skillqueue);
        }

        // Calculate the progress percentage for each skill individually
        var totalProgressPercent = 0;
        var skillCount = skillqueueJson.length;
        var currentDate = new Date();

        skillqueueJson.forEach(skill => {
            var startDate = new Date(skill.start_date);
            var endDate = new Date(skill.finish_date);
            var skillDuration = endDate - startDate;
            var skillTrainedDuration = Math.min(currentDate - startDate, skillDuration);

            var skillProgressPercent = (skillTrainedDuration / skillDuration) * 100;

            // Ensure the progress percentage is between 0 and 100
            if (!isFinite(skillProgressPercent) || skillProgressPercent < 0) {
                skillProgressPercent = 0;
            } else if (skillProgressPercent > 100) {
                skillProgressPercent = 100;
            }

            totalProgressPercent += skillProgressPercent;
        });

        // Calculate the average progress percentage
        var averageProgressPercent = totalProgressPercent / skillCount;

        // Ensure the final progress percentage is between 0 and 100
        if (!isFinite(averageProgressPercent) || averageProgressPercent < 0) {
            averageProgressPercent = 0;
        } else if (averageProgressPercent > 100) {
            averageProgressPercent = 100;
        }

        return averageProgressPercent;
    }

    function hasActiveTraining(skillqueueJson) {
        const queueJson = JSON.parse(skillqueueJson);
        return queueJson.some(skill => skill.start_date !== null && skill.finish_date !== null);
    }

    // Fetch data using AJAX
    $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            data.forEach(item => {
                const skillList = item.skills;
                item.characters.forEach(character => {
                    const row = [];

                    // Character
                    const characterCell = `
                        <td>
                            <img src="https://images.evetech.net/characters/${character.character_id}/portrait?size=32" class="rounded-circle" style="margin-right: 5px; width: 32px; height: 32px;">
                            ${character.character_name}
                            <i class="fa-solid fa-bullhorn" style="margin-left: 5px; color: ${character.notification ? 'green' : 'red'};" title="${character.notification ? alarmActivated : alarmDeactivated}" data-tooltip-toggle="tooltip"></i>
                        </td>
                    `;

                    // Serialize skills to JSON string
                    const skillqueueFilteredJson = JSON.stringify(character.skillqueuefiltered);
                    const skillqueueJson = JSON.stringify(character.skillqueue);
                    const skillsJson = JSON.stringify(character.skills);

                    const is_extraction_ready = character.extraction_ready;

                    const progressBarHtml = `
                    <div class="progress-outer flex-grow-1 me-2">
                        <div class="progress" style="position: relative;">
                            <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${calculateSumProgressBar(skillqueueFilteredJson, skillsJson)}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);"></div>
                            <div class="progress-value" style="position: absolute; width: 100%; text-align: center;">${calculateSumProgressBar(skillqueueFilteredJson, skillsJson).toFixed(0)}%</div>
                        </div>
                    </div>
                    `;

                    const noActiveTrainingHtml = `
                        <div class="text-danger fw-bold">${noActiveTraining}</div>
                    `;

                    const skillCell = `
                        <td>
                            <div class="d-flex align-items-center">
                                ${hasActiveTraining(skillqueueJson) ? progressBarHtml : noActiveTrainingHtml}
                            </div>
                        </td>
                    `;

                    const skillStatus = is_extraction_ready ? '<img src="/static/skillfarm/images/skillExtractor.png" class="rounded-circle" style="width: 32px">' : '';
                    const skillStatusWarning = is_extraction_ready ? 'bg-warning' : '';
                    const skillListHtml = `
                        <button class="btn btn-primary btn-sm btn-square ${skillStatusWarning}" data-bs-toggle="modal" data-bs-target="#skillQueueModal" data-character-id="${character.character_id}" data-character-name="${character.character_name}" data-skillqueue='${skillqueueFilteredJson}' data-skills='${skillsJson}' onclick="showskillQueueModal(this)">
                            <span class="fas fa-info"></span>
                        </button>
                        ${skillStatus}
                    `;

                    // Last Updated
                    const lastUpdatedCell = character.last_update
                        ? `<td data-order="${new Date(character.last_update).getTime()}">${new Date(character.last_update).toLocaleString()}</td>`
                        : `<td>${notupdated}</td>`;

                    // Filter Status
                    const filterstatusCell = `
                        <td>
                            <img src="/static/skillfarm/images/${character.skillset && character.skillset.length > 0 ? 'green' : 'red'}.png" style="width: 24px; height: 24px;" title="${character.skillset && character.skillset.length > 0 ? 'Active' : 'Inactive'}" data-tooltip-toggle="tooltip">
                        </td>
                    `;

                    // Actions
                    const actionsCell = `
                        <td>
                            <form class="d-inline" method="post" action="${switchAlarmUrl(character.character_id)}" id="switchAlarmForm${character.character_id}">
                                ${csrfToken}
                                <input type="hidden" name="character_pk" value="${characterPk}">

                                <button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="${switchAlarm}" data-bs-target="#confirmModal" data-confirm-text="${switchAlarmText} for ${character.character_name}?" data-form-id="switchAlarmForm${character.character_id}">
                                    <span class="fas fa-bullhorn"></span>
                                </button>
                            </form>

                            <form class="d-inline" method="post" action="${switchSkillSetpUrl(character.character_id)}" id="switchSkillSetForm${character.character_id}">
                                ${csrfToken}
                                <button type="button" class="btn btn-warning btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="${switchSkillset}" data-bs-target="#switchSkillSetModal" data-character-id="${character.character_id}" data-character-name="${character.character_name}" data-skills="${skillList}" data-skillset="${character.skillset}">
                                    <span class="fas fa-pencil"></span>
                                </button>
                            </form>

                            <form class="d-inline" method="post" action="${deleteCharUrl(character.character_id)}" id="deleteCharForm${character.character_id}">
                                ${csrfToken}
                                <input type="hidden" name="character_pk" value="${characterPk}">

                                <button type="button" class="btn btn-danger btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="${deleteChar}" data-bs-target="#confirmModal" data-confirm-text="${deleteCharConfirm} for ${character.character_name}?" data-form-id="deleteCharForm${character.character_id}">
                                    <span class="fas fa-trash-alt"></span>
                                </button>
                            </form>
                        </td>
                    `;

                    row.push(characterCell, skillCell, skillListHtml, lastUpdatedCell, filterstatusCell, actionsCell);
                    table.row.add(row).draw();
                });
            });

            // Add "Switch All Alarms" button if data exists
            if (data.length > 0) {
                const switchAllAlarmsButton = document.createElement('button');
                switchAllAlarmsButton.textContent = 'Switch All Alarms';
                switchAllAlarmsButton.className = 'btn btn-primary';
                switchAllAlarmsButton.style.marginTop = '10px';
                switchAllAlarmsButton.title = switchAlarm;

                const switchAllAlarmsForm = document.createElement('form');
                switchAllAlarmsForm.method = 'post';
                switchAllAlarmsForm.action = switchAlarmUrl(0);
                switchAllAlarmsForm.id = 'switchAllAlarmsForm';
                switchAllAlarmsForm.className = 'd-inline';
                switchAllAlarmsForm.innerHTML = csrfToken +
                    '<input type="hidden" name="character_pk" value="' + characterPk + '">' +
                    '<button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="'+ switchAlarm +'" data-bs-target="#confirmModal" data-confirm-text="' + switchAlarmText + '?" data-form-id="switchAllAlarmsForm">' + switchAllAlarmsButton.textContent + '</button>';

                const tableContainer = document.querySelector('#skillfarm-details').parentElement;
                const switchAllAlarmsContainer = document.createElement('div');
                switchAllAlarmsContainer.className = 'switch-all-alarms-container';
                switchAllAlarmsContainer.appendChild(switchAllAlarmsForm);
                tableContainer.appendChild(switchAllAlarmsContainer);
            }

            // Reinitialize tooltips on draw
            table.on('draw', function () {
                $('[data-tooltip-toggle="tooltip"]').tooltip();
            });
            // Init tooltips
            $('[data-tooltip-toggle="tooltip"]').tooltip();
        },
        error: function(error) {
            console.error('Error fetching data:', error);
        }
    });



    // Function to update the skill set select options
    function updateSkillSetOptions(searchValue = '') {
        var selectedSkillsList = document.getElementById('selectedSkillsList');
        var selectedSkills = Array.from(selectedSkillsList.querySelectorAll('li')).map(item => item.getAttribute('data-skill'));

        var skillSetSelect = document.getElementById('skillSetSelect');
        var options = skillSetSelect.options;
        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            if (selectedSkills.includes(option.value)) {
                option.style.display = 'none';
            } else if (option.textContent.toLowerCase().includes(searchValue.toLowerCase())) {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        }
    }

    // Handle search and add to list
    document.getElementById('skillSearch').addEventListener('input', function() {
        var searchValue = this.value.toLowerCase();
        updateSkillSetOptions(searchValue);
    });

    // Handle adding selected skill to list
    document.getElementById('skillSetSelect').addEventListener('change', function() {
        var selectedSkill = this.value;
        if (selectedSkill) {
            var selectedSkillsList = document.getElementById('selectedSkillsList');
            var existingItems = selectedSkillsList.querySelectorAll('li');
            var alreadySelected = Array.from(existingItems).some(item => item.getAttribute('data-skill') === selectedSkill);

            if (!alreadySelected) {
                var listItem = document.createElement('li');
                listItem.textContent = selectedSkill;
                listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                listItem.setAttribute('data-skill', selectedSkill);

                // Add remove button
                var removeButton = document.createElement('button');
                removeButton.className = 'btn btn-danger btn-sm';
                removeButton.textContent = 'Remove';
                removeButton.addEventListener('click', function() {
                    selectedSkillsList.removeChild(listItem);
                    updateSkillSetOptions(document.getElementById('skillSearch').value);
                });

                listItem.appendChild(removeButton);
                selectedSkillsList.appendChild(listItem);
                updateSkillSetOptions(document.getElementById('skillSearch').value);
            }
        }
    });
    // Initial call to update options on page load
    updateSkillSetOptions();

    // Handle modal submission
    document.getElementById('submitSkillSet').addEventListener('click', function(event) {
        var characterId = document.querySelector('#switchSkillSetModal').getAttribute('data-character-id');
        var selectedSkillsList = document.getElementById('selectedSkillsList');
        var selectedSkills = [];
        selectedSkillsList.querySelectorAll('li').forEach(function(item) {
            var skill = item.getAttribute('data-skill');
            if (skill && skill.trim() !== '') {
                selectedSkills.push(skill);
            }
        });

        // Create form dynamically
        const switchSkillSetForm = document.createElement('form');
        switchSkillSetForm.method = 'post';
        switchSkillSetForm.action = switchSkillSetpUrl(characterId);
        switchSkillSetForm.id = 'switchSkillSetForm';
        switchSkillSetForm.className = 'd-inline';
        switchSkillSetForm.innerHTML = skillfarmSettings.csrfToken +
            '<input type="hidden" name="character_pk" value="' + characterId + '">' +
            '<input type="hidden" name="skill_set" value="' + selectedSkills.join(',') + '">';

        document.body.appendChild(switchSkillSetForm);
        switchSkillSetForm.submit();
    });

    // Set character ID and populate skills when modal is shown
    $('#switchSkillSetModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var characterId = button.data('character-id');
        var characterName = button.data('character-name');
        var skills = button.data('skills');
        var skillsetJson = button.data('skillset');

        var modal = $(this);
        modal.attr('data-character-id', characterId);

        // Update modal title
        var modalTitle = modal.find('.modal-title');
        modalTitle.text(`Skill Set Filter - ${characterName}`);

        // Convert skills and skillsetJson to arrays if they are comma-separated strings and not empty
        if (typeof skills === 'string') {
            skills = skills.split(',');
        } else {
            skills = null;
        }

        if (typeof skillsetJson === 'string') {
            skillsetJson = skillsetJson.split(',');
        } else {
            skillsetJson = null;
        }

        // Populate skill set select options
        var skillSetSelect = document.getElementById('skillSetSelect');
        skillSetSelect.innerHTML = '';

        if (!skills) {
            var option = document.createElement('option');
            option.value = '';
            option.textContent = 'No Skill Filter active';
            skillSetSelect.appendChild(option);
        } else {
            skills.forEach(skill => {
                var option = document.createElement('option');
                option.value = skill;
                option.textContent = skill;
                skillSetSelect.appendChild(option);
            });
        }

        // Populate selected skills list with active skill filters
        var selectedSkillsList = document.getElementById('selectedSkillsList');
        selectedSkillsList.innerHTML = '';
        if (skillsetJson && skillsetJson.length > 0) {
            skillsetJson.forEach(skill => {
                if (skill.trim() !== '') {
                    var listItem = document.createElement('li');
                    listItem.textContent = skill;
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    listItem.setAttribute('data-skill', skill);

                    // Add remove button
                    var removeButton = document.createElement('button');
                    removeButton.className = 'btn btn-danger btn-sm';
                    removeButton.textContent = 'Remove';
                    removeButton.addEventListener('click', function() {
                        selectedSkillsList.removeChild(listItem);
                        updateSkillSetOptions();
                    });

                    listItem.appendChild(removeButton);
                    selectedSkillsList.appendChild(listItem);
                }
            });
        }
    });
});

function showskillQueueModal(button) {
    const characterName = button.getAttribute('data-character-name');
    const skillQueue = JSON.parse(button.getAttribute('data-skillqueue'));
    const skills = JSON.parse(button.getAttribute('data-skills'));

    const skillqueueInfo = skillfarmSettings.skillqueueInfoText;

    const modalTitle = document.querySelector('#skillQueueModalLabel');
    modalTitle.textContent = `${skillqueueInfo} - ${characterName}`;

    const modalBody = document.querySelector('#skillQueueModal .modal-body');
    modalBody.innerHTML = ''; // Clear previous content

    // Create skill queue header
    const skillQueueHeader = document.createElement('h3');
    skillQueueHeader.textContent = 'Skill Queue';
    modalBody.appendChild(skillQueueHeader);

    // Create skill queue table
    const skillQueueTable = document.createElement('table');
    skillQueueTable.className = 'table table-striped';
    skillQueueTable.id = 'skillqueueTable';

    // Create skill queue table header
    const skillQueueThead = document.createElement('thead');
    skillQueueThead.innerHTML = `
        <tr>
            <th>Skill</th>
            <th class="no-sort">Progress</th>
            <th>Start Date</th>
            <th>Finish Date</th>
        </tr>
    `;
    skillQueueTable.appendChild(skillQueueThead);

    // Create skill queue table body
    const skillQueueTbody = document.createElement('tbody');

    // Populate skill queue table body with skills
    skillQueue.forEach(skill => {
        // Calculate progress
        var totalSP = skill.end_sp;
        var gainedSP = skill.start_sp;
        var trainedSP = skill.trained_sp;
        var startDate = new Date(skill.start_date);
        var endDate = new Date(skill.finish_date);
        const currentDate = new Date();

        // Set progressPercent to 0 if trainedSP is equal to gainedSP
        let progressPercent = 0;
        if (currentDate > endDate) {
            progressPercent = 100;
        } else if (currentDate < startDate) {
            let totalDuration = endDate - startDate;
            let elapsedDuration = currentDate - startDate;
            progressPercent = (elapsedDuration / totalDuration) * 100;
        } else if (currentDate > startDate) {
            let totalDuration = endDate - startDate;
            let elapsedDuration = currentDate - startDate;
            progressPercent = (elapsedDuration / totalDuration) * 100;
        } else if (gainedSP !== trainedSP) {
            progressPercent = (trainedSP / totalSP) * 100;
        }

        // Ensure it cannot be less than 0
        if (progressPercent < 0) {
            progressPercent = 0;
        }

        if (!skill.is_active && !skill.start_date) {
            progressPercent = 0;
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${skill.skill}</td>
            <td>
                <div class="progress" style="position: relative;">
                    <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: ${progressPercent}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);" aria-valuenow="${progressPercent}" aria-valuemin="0" aria-valuemax="100"></div>
                    <div class="progress-value" style="position: absolute; width: 100%; text-align: center;">${progressPercent.toFixed(0)}%</div>
                </div>
            </td>
            <td data-order="${skill.is_active ? new Date(skill.start_date).getTime() : ''}">
                ${skill.start_date ? new Date(skill.start_date).toLocaleString() : '-'}
            </td>
            <td data-order="${skill.is_active ? new Date(skill.finish_date).getTime() : ''}">
                ${skill.start_date ? new Date(skill.finish_date).toLocaleString() : '-'}
            </td>
        `;
        skillQueueTbody.appendChild(tr);
    });

    skillQueueTable.appendChild(skillQueueTbody);
    modalBody.appendChild(skillQueueTable);

    // Check if skills data is not empty
    if (skills.length > 0) {
        // Add separator
        const separator = document.createElement('hr');
        modalBody.appendChild(separator);

        // Create skills header
        const skillsHeader = document.createElement('h3');
        skillsHeader.textContent = 'Skills';
        modalBody.appendChild(skillsHeader);

        // Create skills table
        const skillsTable = document.createElement('table');
        skillsTable.className = 'table table-striped';
        skillsTable.id = 'skillsTable';

        // Create skills table header
        const skillsThead = document.createElement('thead');
        skillsThead.innerHTML = `
            <tr>
                <th>Skill</th>
                <th>Level</th>
            </tr>
        `;
        skillsTable.appendChild(skillsThead);

        // Create skills table body
        const skillsTbody = document.createElement('tbody');

        // Populate skills table body with skills
        skills.forEach(skill => {
            if (skill.level > 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${skill.skill}</td>
                    <td>${skill.level}</td>
                `;

                // Highlight skills with level 5
                if (skill.level === 5) {
                    tr.classList.add('bg-danger');
                }

                skillsTbody.appendChild(tr);
            }
        });

        skillsTable.appendChild(skillsTbody);
        modalBody.appendChild(skillsTable);
    }

    // Initialize DataTables
    $(document).ready(function() {
        $('#skillqueueTable').DataTable({
            order: [[2, 'asc']],
            pageLength: 10,
            columnDefs: [
                { 'orderable': false, 'targets': 'no-sort' }
            ],
        });

        if (skills.length > 0) {
            $('#skillsTable').DataTable({
                order: [[0, 'asc']],
                pageLength: 10,
            });
        }
    });
}
