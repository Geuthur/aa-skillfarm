/* global aaSkillfarmSettings, aaSkillfarmSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, SlimSelect */
$(document).ready(() => {

    /**
     * Table IDs :: Skillfarm
     */
    const SkillfarmDetailsTable = $('#skillfarm-details');
    const SkillfarmInactiveTable = $('#skillfarm-inactive');
    const SkillfarmQueueTable = $('#skillfarm-skillqueue');
    const SkillfarmQueueFilteredTable = $('#skillfarm-skillqueue-filtered');
    const SkillfarmSkillsTable = $('#skillfarm-skills');

    /**
     * Reload Skillfarm DataTables
     *
     * @param {Object} tableData # Ajax API Response Data
     * @private
     */
    const _reloadSkillFarmDataTable = (tableData) => {
        const dtActive = SkillfarmDetailsTable.DataTable();
        dtActive.clear().rows.add(tableData.active_characters).draw();
        // Inactive Table
        const dtInactive = SkillfarmInactiveTable.DataTable();
        dtInactive.clear().rows.add(tableData.inactive_characters).draw();
        // reload Extractor Count
        $('#skillExtractorLabel').text(tableData && tableData.skill_extraction_count != null ? tableData.skill_extraction_count : 'N/A');
    };

    fetchGet({
        url: aaSkillfarmSettings.url.Skillfarm.replace('12345', aaSkillfarmSettings.characterPk),
    })
        .then((data) => {
            if (data) {
                // Set extraction count from the full response object
                $('#skillExtractorLabel').text(data && data.skill_extraction_count != null ? data.skill_extraction_count : 'N/A');
                /**
                 * Table :: Active Characters
                 */
                const activeDataTable = new DataTable(SkillfarmDetailsTable, {
                    data: data.active_characters,
                    language: aaSkillfarmSettings.dataTables.language,
                    layout: aaSkillfarmSettings.dataTables.layout,
                    ordering: aaSkillfarmSettings.dataTables.ordering,
                    columnControl: aaSkillfarmSettings.dataTables.columnControl,
                    order: [[0, 'asc']],
                    columns: [
                        { data: 'character.character_html' },
                        { data: 'details.progress' },
                        { data: 'details.is_extraction_ready'},
                        { data: 'details.last_update' },
                        { data: 'details.is_filter'},
                        { data: 'actions'},
                    ],
                    pageLength: 25,
                    columnDefs: [
                        {
                            targets: [2, 4, 5],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [4],
                            width: 45
                        },
                        {
                            targets: [2, 5],
                            width: 115
                        },
                    ],
                    initComplete: function () {
                        _bootstrapTooltip({selector: '#skillfarm-details'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#skillfarm-details'});
                    },
                    rowCallback: function (row, data, index) {
                        const details = data && data.details;
                        const status = details && details.update_status;
                        if (status === 'error') {
                            $(row).addClass('table-stripe-red');
                        } else if (status === 'in_progress') {
                            $(row).addClass('table-stripe-info');
                        } else if (status === 'incomplete' || status === 'token_error') {
                            $(row).addClass('table-stripe-warning');
                        }

                        const extractionFlag = details && details.is_extraction_ready;
                        if (extractionFlag && typeof extractionFlag.includes === 'function') {
                            if (extractionFlag.includes('skillfarm-skill-extractor-maybe')) {
                                $(row).addClass('table-stripe-warning');
                            } else if (extractionFlag.includes('skillfarm-skill-extractor')) {
                                $(row).addClass('table-stripe-red');
                            }
                        }
                    },
                });
                /**
                 * Table :: Inactive Characters
                 */
                const inactiveDataTable = new DataTable(SkillfarmInactiveTable, {
                    data: data.inactive_characters,
                    language: aaSkillfarmSettings.dataTables.language,
                    layout: aaSkillfarmSettings.dataTables.layout,
                    ordering: aaSkillfarmSettings.dataTables.ordering,
                    columnControl: aaSkillfarmSettings.dataTables.columnControl,
                    order: [[0, 'asc']],
                    columns: [
                        { data: 'character.character_html' },
                        { data: 'details.progress' },
                        { data: 'details.is_extraction_ready', orderable: false },
                        { data: 'details.last_update' },
                        { data: 'details.is_filter', orderable: false },
                        { data: 'actions', orderable: false },
                    ],
                    initComplete: function () {
                        _bootstrapTooltip({selector: '#skillfarm-inactive'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#skillfarm-inactive'});
                    },
                    rowCallback: function (row, data, index) {
                        const details = data && data.details;
                        const status = details && details.update_status;
                        if (status === 'error') {
                            $(row).addClass('table-stripe-red');
                        } else if (status === 'in_progress') {
                            $(row).addClass('table-stripe-info');
                        } else if (status === 'incomplete' || status === 'token_error') {
                            $(row).addClass('table-stripe-warning');
                        }

                        const extractionFlag = details && details.is_extraction_ready;
                        if (extractionFlag && typeof extractionFlag.includes === 'function') {
                            if (extractionFlag.includes('skillfarm-skill-extractor-maybe')) {
                                $(row).addClass('table-stripe-warning');
                            } else if (extractionFlag.includes('skillfarm-skill-extractor')) {
                                $(row).addClass('table-stripe-red');
                            }
                        }

                        if (details && details.is_read === true) {
                            $(row).addClass('opacity-25');
                        }
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Skillfarm DataTable:', error);
        });

    /**
     * SlimSelect :: Skillset
     * @param {string} selector
     * @param {Object} settings
     * @return {SlimSelect}
     */
    let skillSelect = new SlimSelect({
        select: '#skillset',
        settings: {
            hideSelected: true,
            closeOnSelect: false,
            allowDeselect: true,
        }
    });

    /**
     * Load SkillInfo DataTable
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadSkillInfoDataTable = (tableData) => {
        const dtQueue = SkillfarmQueueTable.DataTable();
        dtQueue.clear().rows.add(tableData.skillqueue).draw();
        if (!tableData.skillqueue || tableData.skillqueue.length === 0) {
            $('#table-skillqueue-content').addClass('d-none');
        }
        const dtQueueFiltered = SkillfarmQueueFilteredTable.DataTable();
        dtQueueFiltered.clear().rows.add(tableData.skillqueue_filtered).draw();
        if (!tableData.skillqueue_filtered || tableData.skillqueue_filtered.length === 0) {
            $('#table-skillqueue-filtered-content').addClass('d-none');
        }
        const dtSkills = SkillfarmSkillsTable.DataTable();
        dtSkills.clear().rows.add(tableData.skills).draw();
        if (!tableData.skills || tableData.skills.length === 0) {
            $('#table-skills-content').addClass('d-none');
        }
    };

    /**
     * Clear SkillInfo DataTable
     * @private
     */
    const _clearSkillInfoDataTable = () => {
        const dtQueue = SkillfarmQueueTable.DataTable();
        dtQueue.clear().draw();
        $('#table-skillqueue-content').removeClass('d-none');
        const dtQueueFiltered = SkillfarmQueueFilteredTable.DataTable();
        dtQueueFiltered.clear().draw();
        $('#table-skillqueue-filtered-content').removeClass('d-none');
        const dtSkills = SkillfarmSkillsTable.DataTable();
        dtSkills.clear().draw();
        $('#table-skills-content').removeClass('d-none');
    };

    /**
     * Table :: Skillqueue
     */
    const skillQueueDataTable = new DataTable(SkillfarmQueueTable, {
        data: null, // Loaded via API on modal open
        language: aaSkillfarmSettings.dataTables.language,
        layout: aaSkillfarmSettings.dataTables.layout,
        ordering: aaSkillfarmSettings.dataTables.ordering,
        columnControl: aaSkillfarmSettings.dataTables.columnControl,
        order: [[2, 'asc']],
        columns: [
            { data: 'skill' },
            {
                data: {
                    display: (data) => data.progress.display,
                    sort: (data) => data.progress.sort,
                    filter: (data) => data.progress.sort
                }
            },
            { data: 'start_date'},
            { data: 'finish_date' },
        ],
        columnDefs: [
            { targets: [1], type: 'num' }
        ],
        pageLength: 25,
        rowCallback: function (row, data, index) {
            if (data.progress.sort == 100) {
                $(row).addClass('table-stripe-green');
            }
        },
    });
    /**
     * Table :: Skillqueue Filtered
     */
    const skillQueueFilteredDataTable = new DataTable(SkillfarmQueueFilteredTable, {
        data: null, // Loaded via API on modal open
        language: aaSkillfarmSettings.dataTables.language,
        layout: aaSkillfarmSettings.dataTables.layout,
        ordering: aaSkillfarmSettings.dataTables.ordering,
        columnControl: aaSkillfarmSettings.dataTables.columnControl,
        order: [[3, 'asc']],
        columns: [
            { data: 'skill' },
            {
                data: {
                    display: (data) => data.progress.display,
                    sort: (data) => data.progress.sort,
                    filter: (data) => data.progress.sort
                }
            },
            { data: 'start_date'},
            { data: 'finish_date' },
        ],
        columnDefs: [
            { targets: [1], type: 'num' }
        ],
        pageLength: 25,
        rowCallback: function (row, data, index) {
            if (data.progress.sort == 100) {
                $(row).addClass('table-stripe-green');
            }
        },
    });

    /**
     * Table :: Skills
     */
    const skillsDataTable = new DataTable(SkillfarmSkillsTable, {
        data: null, // Loaded via API on modal open
        language: aaSkillfarmSettings.dataTables.language,
        layout: aaSkillfarmSettings.dataTables.layout,
        ordering: aaSkillfarmSettings.dataTables.ordering,
        columnControl: aaSkillfarmSettings.dataTables.columnControl,
        order: [[1, 'desc']],
        columns: [
            { data: 'skill' },
            { data: 'level' },
            { data: 'skillpoints'},
        ],
        rowCallback: function (row, data, index) {
            if (data.level >= 5) {
                $(row).addClass('table-stripe-red');
            }
        },
    });

    /* Modals */
    const modalRequestSwitchNotification = $('#skillfarm-accept-switch-notification');
    const modalRequestDelete = $('#skillfarm-accept-delete-character');
    const modalRequestViewSkillqueue = $('#skillfarm-view-skillqueue');
    const modalRequestEditSkillsetup = $('#skillfarm-edit-skillsetup');
    const modalRequestMarkAsRead = $('#skillfarm-accept-mark-as-read');

    /**
     * SkillFarm Switch Notification Modal
     */
    modalRequestSwitchNotification.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestSwitchNotification.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestSwitchNotification.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
            })
                .then((data) => {
                    if (data.success === true) {
                        fetchGet({
                            url: aaSkillfarmSettings.url.Skillfarm.replace('12345', aaSkillfarmSettings.characterPk)
                        })
                            .then((newData) => {
                                _reloadSkillFarmDataTable(newData);
                                modalRequestSwitchNotification.modal('hide');
                            })
                            .catch((error) => {
                                console.error('Error fetching Skillfarm DataTable:', error);
                            });
                    }
                })
                .catch((error) => {
                    console.error(`Error posting switch notification request: ${error.message}`);
                });
        });
    }).on('hide.bs.modal', () => {
        modalRequestSwitchNotification.find('#modal-button-confirm-accept-request').unbind('click');
    });

    /**
     * SkillFarm Delete Character Modal
     */
    modalRequestDelete.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDelete.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestDelete.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
            })
                .then((data) => {
                    if (data.success === true) {
                        fetchGet({
                            url: aaSkillfarmSettings.url.Skillfarm.replace('12345', aaSkillfarmSettings.characterPk)
                        })
                            .then((newData) => {
                                _reloadSkillFarmDataTable(newData);
                                modalRequestDelete.modal('hide');
                            })
                            .catch((error) => {
                                console.error('Error fetching Skillfarm DataTable:', error);
                            });
                    }
                })
                .catch((error) => {
                    console.error(`Error posting delete request: ${error.message}`);
                });
        });
    }).on('hide.bs.modal', () => {
        modalRequestDelete.find('#modal-button-confirm-accept-request').unbind('click');
    });

    /**
     * SkillFarm View Skillqueue Modal
     */
    modalRequestViewSkillqueue.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadSkillInfoDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Skillinfo Modal:', error);
            });
    }).on('hide.bs.modal', () => {
        _clearSkillInfoDataTable();
    });

    /**
     * SkillFarm Skillset Modal
     */
    modalRequestEditSkillsetup.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const ApiUrl = button.data('api');
        const form = modalRequestEditSkillsetup.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        /**
         * Fetch Skillset Data and Populate SlimSelect
         */
        fetchGet({
            url: ApiUrl
        })
            .then(data => {
                if (data.setup && data.setup.skillset && Array.isArray(data.setup.skillset)) {
                    skillSelect.setSelected(data.setup.skillset);
                } else {
                    console.log('No skillset found or skillset is not an array');
                }
            })
            .catch((error) => {
                console.error('Error fetching Skillset data:', error);
            });

        modalRequestEditSkillsetup.find('#modal-button-confirm-accept-request').on('click', () => {
            /**
             * Get selected skills and prepare payload
             */
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
                payload: {
                    selected_skills: skillSelect.getSelected()
                },
            })
                .then((data) => {
                    if (data.success === true) {
                        fetchGet({
                            url: aaSkillfarmSettings.url.Skillfarm.replace('12345', aaSkillfarmSettings.characterPk)
                        })
                            .then((newData) => {
                                _reloadSkillFarmDataTable(newData);
                                modalRequestEditSkillsetup.modal('hide');
                            })
                            .catch((error) => {
                                console.error('Error fetching Skillfarm DataTable:', error);
                            });
                    }
                })
                .catch((error) => {
                    console.error(`Error posting edit skillsetup request: ${error.message}`);
                });
        });
    }).on('hide.bs.modal', () => {
        // Clear the modal content and reset input fields
        skillSelect.setSelected([]);
        modalRequestEditSkillsetup.find('input[name="selected_skills"]').val('');
        modalRequestEditSkillsetup.find('#modal-button-confirm-accept-request').unbind('click');
    });


    /**
     * SkillFarm Mark As Read Modal
     */
    modalRequestMarkAsRead.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestMarkAsRead.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestMarkAsRead.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
            })
                .then((data) => {
                    if (data.success === true) {
                        fetchGet({
                            url: aaSkillfarmSettings.url.Skillfarm.replace('12345', aaSkillfarmSettings.characterPk)
                        })
                            .then((newData) => {
                                _reloadSkillFarmDataTable(newData);
                                modalRequestMarkAsRead.modal('hide');
                            })
                            .catch((error) => {
                                console.error('Error fetching Skillfarm DataTable:', error);
                            });
                    }
                })
                .catch((error) => {
                    console.error(`Error posting mark as read request: ${error.message}`);
                });
        });
    }).on('hide.bs.modal', () => {
        modalRequestMarkAsRead.find('#modal-button-confirm-accept-request').unbind('click');
    });
});
