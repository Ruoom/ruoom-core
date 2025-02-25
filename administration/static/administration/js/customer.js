$(document).ready(function () {
    $("#searchcustomer").focus(function(){
        $("#customercard").hide()
        $("#customer_update_form").trigger("reset");
        $("#classes_table").bootstrapTable("destroy");
        $(".error-msg").hide();
        $(".error-msg").empty();
        customer_tables_rows = $("#customer_table tbody tr");
        for (var c=0; c < customer_tables_rows.length; c++){
            $($("#customer_table tbody tr")[c]).css('display','table-row');
        }
    });

    $("#searchcustomer").autocomplete({
        source: "search/",
        minLength: 1,
        open: function(){
            setTimeout(function () {
                $(".ui-autocomplete").css("z-index", 99);
            }, 0);
        },
        select: function(event, ui) {
            showInfoTab();
            $('#searchcustomer').blur();
            $("#cardinfo").addClass("active");
            $("#customercard").show()
            $("#customerSetup").show()
            $('.header-title-customer').text(ui.item.localized_name)
            $('#name').text(ui.item.localized_name)
            $('#gender').text(ui.item.gender);
            $('#dob').text(ui.item.dob)
            $('#email').text(ui.item.email)
            $('#streetAddress').text(ui.item.street_address)
            $('#city').text(ui.item.city)
            $('#state').text(ui.item.state)
            $('#phone').text(ui.item.phone)
            $('#emergencyContactName').text(ui.item.emgcy_cont_name);
            customer_tables_rows = $("#customer_table tbody tr");
            for (var c=0; c < customer_tables_rows.length; c++){
                if(ui.item.email == $("#customer_table tbody tr")[c].id){
                    $($("#customer_table tbody tr")[c]).css('display','table-row');
                }else{
                    $($("#customer_table tbody tr")[c]).css('display','none');
                }
            }
        }
    });

    $( "#customer_update_form" ).submit(function(e) {
        $(".error-msg").hide();
        $(".error-msg").empty();
        e.preventDefault();
        var form =$(this);
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
        if("success" in data){
            $("#response-info").removeClass("alert-danger");
            $("#response-info").addClass("alert-success");
            $("#response-info").append("<b>Success:</b>" + data["success"]);
            $("#response-info").show();
            var first_name = $("#customer_first_name_form").val();
            var last_name = $("#customer_last_name_form").val();
            var email = $("#customer_email_form").val();
            var phone = $("#customer_phone_form").val();
            var emg_num = $("#customer_emg_num_form").val();
            var emg_name = $("#customer_emg_name_form").val();
            $("#searchcustomer").val(first_name + " " + last_name);
            $("#card_customer_name").text(first_name + " " + last_name);
            $("#customer_first_name").text(first_name);
            $("#customer_last_name").text(last_name);
            $("#customer_email").text(email);
            $("#customer_phone").text(phone);
            $("#customer_emg_num").text(emg_num);
            $("#customer_emg_name").text(emg_name);
        }else{
            $("#response-info").removeClass("alert-success");
            $("#response-info").addClass("alert-danger");
            $("#response-info").append("<b>Errors!</b>");
            errors = data["error"];
            for (var key in errors) {
                if (errors.hasOwnProperty(key)) {
                    field_errors = errors[key];
                    for (index = 0; index < field_errors.length; index++) {
                        $("#"+key+"_error_msg").append("<p> " + field_errors[index] +"</p>");
                    }
                    $("#"+key+"_error_msg").show()
                }
            }
            $("#response-info").show();
        }
    }
});

function showInfoTab() {
    $("#cardinfo").addClass("active");
    $("#cardedit").removeClass("active");
    $("#cardclasses").removeClass("active");
    $("#customerinfo").show();
    $("#customerclasses").hide();
    $("#customereditinfo").hide();

}

function showClassesTab(){
    $("#cardinfo").removeClass("active");
    $("#cardedit").removeClass("active");
    $("#cardclasses").addClass("active");
    $("#customerinfo").hide();
    $("#customereditinfo").hide();
    $("#customerclasses").show();
}

function showEditInfoTab() {
    $("#cardclasses").removeClass("active");
    $("#cardinfo").removeClass("active");
    $("#cardedit").addClass("active");
    $("#customerinfo").hide();
    $("#customerclasses").hide();
    $("#customereditinfo").show();

}