/* global SkillfarmSettings bootstrap */

$(document).ready(() => {
    const OverView = $('#skillfarm-overview');
    const OverViewTable = OverView.DataTable({
        ajax: {
            url: SkillfarmSettings.OverviewUrl,
            type: 'GET',
            dataSrc: function (data) {
                return Object.values(data);
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                OverViewTable.clear().draw();
            }
        },
        columns: [
            {
                data: 'portrait',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'character_name',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'corporation_name',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'action',
                className: 'text-end',
                render: function (data, _, row) {
                    return data;
                }
            }
        ],
        order: [[1, 'asc']],
        columnDefs: [
            { orderable: false, targets: [0, 3] },
        ],
    });

    OverViewTable.on('draw', function (row, data) {
        $('[data-tooltip-toggle="skillfarm-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
