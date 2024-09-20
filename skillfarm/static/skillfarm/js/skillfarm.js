/* global skillfarmSettings */
/* global bootstrap */

document.addEventListener('DOMContentLoaded', function() {
    var csrfToken = skillfarmSettings.csrfToken;
    var urlAlarm = skillfarmSettings.switchAlarmUrl;
    var url = skillfarmSettings.skillfarmUrl;
    var characterPk = skillfarmSettings.characterPk;
    // Translations
    var switchAlarmText = skillfarmSettings.switchAlarmConfirmText;
    var switchAlarm = skillfarmSettings.switchAlarmText;
    var alarmActivated = skillfarmSettings.alarmActivatedText;
    var alarmDeactivated = skillfarmSettings.alarmDeactivatedText;
    var notupdated = skillfarmSettings.notUpdatedText;

    function switchAlarmUrl(characterId) {
        return urlAlarm
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
        order: [[3, 'desc']],
        pageLength: 25,
        columnDefs: [
            { 'orderable': false, 'targets': 'no-sort' }
        ],
        createdRow: function(row, data, dataIndex) {
            $('td:eq(4)', row).addClass('text-end');
        }
    });

    // Fetch data using AJAX
    $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            const characterIds = new Set();

            data.forEach(item => {
                characterIds.add(item.character_id);
                const row = [];

                // Character
                const characterCell = `
                    <td>
                        <img src="https://images.evetech.net/characters/${item.character_id}/portrait?size=32" class="rounded-circle" style="margin-right: 5px; width: 32px; height: 32px;">
                        ${item.character_name}
                        <i class="fa-solid fa-bullhorn" style="margin-left: 5px; color: ${item.notification ? 'green' : 'red'};" title="${item.notification ? alarmActivated : alarmDeactivated}" data-tooltip-toggle="tooltip"></i>
                    </td>
                `;

                // Serialize skills to JSON string
                const skillsJson = JSON.stringify(item.skills);

                const skillCell = `
                    <td>
                        <button class="btn btn-primary btn-sm btn-square" style="margin-left: 5px;" data-bs-toggle="modal" data-bs-target="#skillInfoModal" data-character-id="${item.character_id}" data-character-name="${item.character_name}" data-skills='${skillsJson}' onclick="showSkillInfoModal(this)">
                            <span class="fas fa-info"></span>
                        </button>
                    </td>
                `;

                // Status
                const statusCell = `
                    <td>
                        <img src="/static/skillfarm/images/${item.active ? 'green' : 'red'}.png" style="width: 24px; height: 24px;" title="${item.active ? 'Active' : 'Inactive'}" data-tooltip-toggle="tooltip">
                    </td>
                `;

                // Last Updated
                const lastUpdatedCell = item.last_update
                    ? `<td>${new Date(item.last_update).toLocaleString()}</td>`
                    : `<td>${notupdated}</td>`;

                // Actions
                const actionsCell = `
                    <td>
                        <form class="d-inline" method="post" action="${switchAlarmUrl(item.character_id)}" id="switchAlarmForm${item.character_id}">
                            ${csrfToken}
                            <input type="hidden" name="character_pk" value="${characterPk}">
                            <button type="button" class="btn btn-primary btn-sm btn-square" data-bs-toggle="modal" data-tooltip-toggle="tooltip" title="${switchAlarm}" data-bs-target="#confirmModal" data-confirm-text="${switchAlarmText} for ${item.character_name}?" data-form-id="switchAlarmForm${item.character_id}">
                                <span class="fas fa-bullhorn"></span>
                            </button>
                        </form>
                    </td>
                `;

                row.push(characterCell, skillCell, statusCell, lastUpdatedCell, actionsCell);
                table.row.add(row).draw();
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
});

function showSkillInfoModal(button) {
    const characterName = button.getAttribute('data-character-name');
    const skills = JSON.parse(button.getAttribute('data-skills'));
    const skillqueueInfo = skillfarmSettings.skillqueueInfoText;

    const modalTitle = document.querySelector('#skillInfoModalLabel');
    modalTitle.textContent = `${skillqueueInfo} - ${characterName}`;

    const modalBody = document.querySelector('#skillInfoModal .modal-body');
    modalBody.innerHTML = ''; // Clear previous content

    // Create table
    const table = document.createElement('table');
    table.className = 'table table-striped';

    // Create table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Skill</th>
            <th>Progress</th>
            <th>Start Date</th>
            <th>Finish Date</th>
        </tr>
    `;
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');

    // Populate table body with skills
    skills.forEach(skill => {
        // Calculate progress
        const totalSP = skill.end_sp;
        const gainedSP = skill.start_sp;
        const trainedSP = skill.trained_sp;

        // Set progressPercent to 0 if trainedSP is equal to gainedSP
        let progressPercent = 0;
        if (gainedSP !== trainedSP) {
            progressPercent = (trainedSP / totalSP) * 100;
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
            <td>${new Date(skill.start_date).toLocaleString()}</td>
            <td>${new Date(skill.finish_date).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    modalBody.appendChild(table);
}
