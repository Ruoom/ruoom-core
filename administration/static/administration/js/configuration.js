$(document).ready(function () {

    $('.waiver_button').click(function() {
        location.reload();
    });

    $('[data-toggle="tooltip"]').hover(function(){$(this).popover('show')}, function(){$(this).popover('hide')})

    /**
    * This is an ajax call for auto filling the dimensions upon selection
    */

    $("#id_room").on('change', function() {
             var room_id = this.value;
             var url = $("#ajax_for_selected_room_on_modal").val();

              $.ajax({
                url: url,
                data: {
                  'room_id': room_id
                },
                dataType: 'json',
                success: function (data) {
                    console.log(data);
                    $("#room_dimensions").val(data.dimensions);
                },
                failure: function(data)
                {
                    alert('There appears to be an error. Please reload and try again');
                }
          });
    });

$(document).ready(function() {
    if (!tour.ended() != false){
        tour.start()
    }
})