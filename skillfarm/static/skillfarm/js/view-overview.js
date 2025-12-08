/* global aaSkillfarmSettings, aaSkillfarmSettingsOverride, _bootstrapTooltip, fetchGet, DataTable */

$(document).ready(() => {
    'use strict';

    /**
     * Table IDs :: Skillfarm
     */
    const OverviewTable = $('#skillfarm-overview');

    /**
     * Table :: Overview
     * @type {*|jQuery|HTMLElement}
     */
    fetchGet({
        url: aaSkillfarmSettings.url.Overview,
    })
        .then((data) => {
            if (data) {
            /**
             * Table :: Overview
             */
                const overviewDataTable = new DataTable(OverviewTable, {
                    data: data.characters,
                    language: aaSkillfarmSettings.dataTables.language,
                    layout: aaSkillfarmSettings.dataTables.layout,
                    ordering: aaSkillfarmSettings.dataTables.ordering,
                    columnControl: aaSkillfarmSettings.dataTables.columnControl,
                    columns: [
                        {
                            data: 'portrait',
                        },
                        {
                            data: {
                                display: (data) => data.character.character_name,
                                sort: (data) => data.character.character_name,
                                filter: (data) => data.character.character_name
                            }
                        },
                        {
                            data: {
                                display: (data) => data.character.corporation_name,
                                sort: (data) => data.character.corporation_name,
                                filter: (data) => data.character.corporation_name
                            }
                        },
                        {
                            data: 'action',
                            className: 'text-end',
                        }
                    ],
                    columnDefs: [
                        {
                            orderable: false,
                            targets: [0, 3],
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },

                    ],
                    order: [[1, 'asc']],
                    initComplete: function () {
                        _bootstrapTooltip({selector: '#skillfarm-overview'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#skillfarm-overview'});
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Overview DataTable:', error);
        });
});
