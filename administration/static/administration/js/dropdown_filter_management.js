$('.option_dropdown').on('change', function() {
    var option_val =  $(this).val();
    var option_text = $(this).find("option:selected").text();
    var is_avail = false
    var data_string = '';
    if (option_val !== "") {
        ignore_close = false;
        $('.dropdown_option_tag').each(function() {

            if ($(this).clone().children().remove().end().text() === option_text) {
                is_avail = true
            }
        });
        if(this.id == 'location_filter'){
            data_string = 'data-filter="location" data-id='+option_val; 
            $('.dropdown_option_tag[data-filter="location"]').remove()
            if(option_val == default_location){
                ignore_close = true;
            }
            var tz_string = $(this).find("option:selected").attr('data-tz');
            option_text += " (" + tz_string + ")";
        }
        else if(this.id == 'service_filter'){
            data_string = 'data-filter="service" data-id='+option_val; 
        }
        else if(this.id == 'service_provider_filter'){
            data_string = 'data-filter="service_provider" data-id='+option_val; 
        }
        if (!is_avail) {
            if(ignore_close){
                $('.dropdown_option_tag').last().after("<span class='badge badge-soft-secondary dropdown_option_tag dropdown_options' "+data_string+">"+ option_text +"</span>");
            }else{
                $('.dropdown_option_tag').last().after("<span class='badge badge-soft-secondary dropdown_option_tag dropdown_options' "+data_string+">"+ option_text +"<span class='badge_close_custom close'>×</span></span>");
            }
            $('.clear-all-btn').css('display', 'inline-block')
            get_class_content('current');
        }
    }

});




$(document).on( 'click', '.badge_close_custom', function() {
	console.log("This is clicked");
    $(this).parent().remove();
    if ($('.dropdown_options').length === 0) {
        $('.clear-all-btn').css('display', 'none')
    }
    if($('.dropdown_option_tag[data-filter="location"]').length == 0){
        $('#location_filter').val(default_location).change();
    }
    get_class_content('current');
});


$('.clear-all-btn').on('click', function() {

    $('.dropdown_options').each(function() {
        $(this).remove();
    })
    $('.clear-all-btn').css('display', 'none')
    $('#location_filter').val(default_location).change();
    get_class_content('current');

})