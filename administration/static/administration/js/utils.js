function replaceDurationTextField() {
    var DURATION_FIELD = 'input#id_duration';

    var oldValue = $(DURATION_FIELD).val();

    if (oldValue) {
        var oldHours = oldValue.split(':')[0];

        var oldMins = oldValue.split(':')[1];
    }

    var newFields = `
    <label>${gettext("Duration:")}</label>
    <div class='row'>
    <div class='col-sm-6'>
    <input class=form-control min=0 max=23 type=number required id=id_duration_hours placeholder="${gettext("hours")}" value=${oldHours || ''}>
    :<input class=form-control min=0 max=59 type=number id=id_duration_mins placeholder="${gettext("minutes")}" value=${oldMins || ''}>
    </div>
    </div>
    `;

    $(DURATION_FIELD).parent().html(newFields);
}

function formatDatetime(datetime) {
    var dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return datetime.toLocaleDateString('en-US', dateOptions) + ' ' + datetime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}
