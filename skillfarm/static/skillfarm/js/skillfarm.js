/* global SkillfarmSettings */

const SkillFarmAjax = (() => {
    const updateDataTable = (tableId, data) => {
        const table = $(tableId);
        if ($.fn.DataTable.isDataTable(table)) {
            table.DataTable().clear().rows.add(data).draw();
        } else {
            table.DataTable({
                data: data,
                columns: [
                    { data: 'character.character_html' },
                    { data: 'details.progress' },
                    { data: 'details.is_extraction_ready', orderable: false },
                    { data: 'details.last_update' },
                    { data: 'details.is_filter', orderable: false },
                    { data: 'actions', orderable: false },
                ],
                order: [[0, 'asc']],
                pageLength: 25,
                initComplete: function () {
                    $('[data-tooltip-toggle="skillfarm-tooltip"]').tooltip({
                        trigger: 'hover',
                    });
                },
                drawCallback: function () {
                    $('[data-tooltip-toggle="skillfarm-tooltip"]').tooltip({
                        trigger: 'hover',
                    });
                },
                rowCallback: function (row, data, index) {
                    if (data.details.is_extraction_ready.includes('skillfarm-skill-extractor-maybe')) {
                        $(row).addClass('table-stripe-warning');
                    } else if (data.details.is_extraction_ready.includes('skillfarm-skill-extractor')) {
                        $(row).addClass('table-stripe-red');
                    }
                },
            });
        }
    };

    const fetchDetails = () => {
        return $.ajax({
            url: SkillfarmSettings.DetailsUrl,
            type: 'GET',
            success: function (data) {
                updateDataTable('#skillfarm-details', Object.values(data.details));
                updateDataTable('#skillfarm-inactive', Object.values(data.inactive));
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
            }
        });
    };

    return {
        fetchDetails,
    };
})();

$(document).ready(() => {
    SkillFarmAjax.fetchDetails();
});
