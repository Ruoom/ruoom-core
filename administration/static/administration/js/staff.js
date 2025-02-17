$(document).ready(function () {

    if ($.find('#id_due_date').length) {
        $('#id_due_date')[0].flatpickr({
            enableTime: true,
            dateFormat: "Y-m-d",
        });
    }

    if ($.find('#id_scheduled_time').length) {
        $('#id_scheduled_time')[0].flatpickr({
            enableTime: true,
            dateFormat: "Y-m-d H:i",
        })
    }
    replaceDurationTextField();

    $('input#id_duration').mask('00:00');
    $("#search_staff").autocomplete({
        source: "search/",
        minLength: 0,
        open: function () {
            setTimeout(function () {
                $(".ui-autocomplete").css("z-index", 99);
            }, 0);
        },
        select: function (event, ui) {
            changeStaff()
            showInfoTab()
            $('#search_staff').blur();
            $("#classes_button").hide()
            $("#staffcard").show()
            $("#card_staff_name").text(ui.item.label);
            $("#staff_first_name").text(ui.item.first_name);
            $("#staff_last_name").text(ui.item.last_name);
            $("#staff_email").text(ui.item.email);
            $("#staff_phone").text(ui.item.phone);
            $("#staff_emg_num").text(ui.item.emgcy_cont_num);
            $("#staff_emg_name").text(ui.item.emgcy_cont_name);
            $("#staff_id_form").val(ui.item.id);
            $("#staff_first_name_form").val(ui.item.first_name);
            $("#staff_last_name_form").val(ui.item.last_name);
            $("#staff_email_form").val(ui.item.email);
            $("#staff_phone_form").val(ui.item.phone);
            $("#staff_emg_num_form").val(ui.item.emgcy_cont_num);
            $("#staff_emg_name_form").val(ui.item.emgcy_cont_name);
            $("#staff_is_teacher_form").prop('checked', ui.item.is_teacher);
            if (ui.item.is_teacher) {
                $("#classes_button").show()
            }
            $('#classes_table').bootstrapTable({
                data: ui.item.classes
            });
        }
    }).focus(function () {
        $(this).autocomplete("search", $(this).val());
    });

    $("#staff_update_form").submit(function (e) {
        $(".error-msg").hide();
        $(".error-msg").empty();
        e.preventDefault();
        var form = $(this);
        var url = form.attr("action");
        var method = form.attr("method");

        $.ajax({
            type: method,
            url: url,
            data: form.serializeArray(),
            success: handle_response,
            error: function (errorThrown) {
                alert(errorThrown);
            }
        })
    });

    function handle_response(data) {
        if ("success" in data) {
            $("#response-info").removeClass("alert-danger");
            $("#response-info").addClass("alert-success");
            $("#response-info").append("<b>Success:</b>" + data["success"]);
            $("#response-info").show();
            var first_name = $("#staff_first_name_form").val();
            var last_name = $("#staff_last_name_form").val();
            var email = $("#staff_email_form").val();
            var phone = $("#staff_phone_form").val();
            var emg_num = $("#staff_emg_num_form").val();
            var emg_name = $("#staff_emg_name_form").val();
            $("#search_staff").val(first_name + " " + last_name);
            $("#card_staff_name").text(first_name + " " + last_name);
            $("#staff_first_name").text(first_name);
            $("#staff_last_name").text(last_name);
            $("#staff_email").text(email);
            $("#staff_phone").text(phone);
            $("#staff_emg_num").text(emg_num);
            $("#staff_emg_name").text(emg_name);
        } else {
            $("#response-info").removeClass("alert-success");
            $("#response-info").addClass("alert-danger");
            $("#response-info").append("<b>Errors!</b>");
            errors = data["error"];
            for (var key in errors) {
                if (errors.hasOwnProperty(key)) {
                    field_errors = errors[key];
                    for (index = 0; index < field_errors.length; index++) {
                        $("#" + key + "_error_msg").append("<p> " + field_errors[index] + "</p>");
                    }
                    $("#" + key + "_error_msg").show()
                }
            }
            $("#response-info").show();
        }
    };

    $('#AddShift').click(function(event){
        $("#shift_error_duration" ).empty();
        $("#shift_error_note" ).empty();
        $("#shift_error_time" ).empty();
        $("#shift_error_staff_member" ).empty();

        var hours= $('#id_duration_hours').val();
        var mins= $('#id_duration_mins').val();
        var note=$('#id_notes').val();
        var scheduled_time=$('#id_scheduled_time').val();
        var staff_member=$('#id_staff_member').val();

        if(hours!="" && mins!=""){
            var durationValue = hours + ':' + mins +":00";
            $('input#id_duration').remove()
            $('<input />')
                .attr('id', 'id_duration')
                .attr('name', 'duration')
                .attr('value', durationValue)
                .attr('hidden', true)
                .appendTo('form#create_shift_form')
        }
        else{
            $('input#id_duration_mins.form-control').after(" <div id='shift_error_duration' style='color:red;'>Duration is required</div>");
        }
        if(note==""){
            $('input#id_notes.form-control').after(" <div id='shift_error_note' style='color:red;'>Note is required</div>");
        }
        if(scheduled_time==""){
            $('input#id_scheduled_time.form-control').after(" <div id='shift_error_time' style='color:red;'>Scheduled time is required</div>");
        }
        if(staff_member==""){
            $('select#id_staff_member.form-control').after(" <div id='shift_error_staff_member' style='color:red;'>Staff member is required</div>");
        }
        return true;
    });
    var today_date = moment();
    $('#tableMonth option[value="'+(parseInt(today_date.format('MM')) - 1).toString()+'"]').attr("selected", "selected");
    $("#tableYear").text(today_date.format('YYYY'));
});

function changeStaff() {
    $("#staffcard").hide()
    $("#staff_update_form").trigger("reset");
    $("#classes_table").bootstrapTable("destroy");
    $(".error-msg").hide();
    $(".error-msg").empty();
}

function showInfoTab() {
    $("#cardinfo").addClass("active");
    $("#cardedit").removeClass("active");
    $("#cardclasses").removeClass("active");
    $("#staffinfo").show();
    $("#staffclasses").hide();
    $("#staffeditinfo").hide();

}

function showClassesTab() {
    $("#cardinfo").removeClass("active");
    $("#cardedit").removeClass("active");
    $("#cardclasses").addClass("active");
    $("#staffinfo").hide();
    $("#staffeditinfo").hide();
    $("#staffclasses").show();
}

function showEditInfoTab() {
    $("#cardclasses").removeClass("active");
    $("#cardinfo").removeClass("active");
    $("#cardedit").addClass("active");
    $("#staffinfo").hide();
    $("#staffclasses").hide();
    $("#staffeditinfo").show();

}
