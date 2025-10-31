/* global SkillfarmSettings bootstrap */

$(document).ready(() => {
    const OverView = $('#skillfarm-overview');
    const OverViewTable = OverView.DataTable({
        ajax: {
            url: SkillfarmSettings.OverviewUrl,
            type: 'GET',
            dataSrc: function (data) {
                return data.characters;
            },
            error: function (xhr, error, thrown) {
                let errorMsg = 'Unknown error';
                try {
                    const resp = JSON.parse(xhr.responseText);
                    errorMsg = resp.error || errorMsg;
                } catch (e) {
                    errorMsg = xhr.responseText || errorMsg;
                }
                console.error('Error loading data:', errorMsg);
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
                data: 'character.character_name',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'character.corporation_name',
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
