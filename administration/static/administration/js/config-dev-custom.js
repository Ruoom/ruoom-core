var closebtns = document.getElementsByClassName("badge_close");
var i;

for (i = 0; i < closebtns.length; i++) {
  closebtns[i].addEventListener("click", function() {
    this.parentElement.style.display = 'none';
  });
}





// GET Location......................................................................................................................................
$(function() {
  $('.select-location').change(function(){
    store_location = $(this).val();
    split_location = store_location.split("location-")[1];

      $('.option1').hide();
      $('#' + $(this).val()).show();

        $.ajax({
          type: 'get',
          url: '/administration/planner/',
          contentType: "application/json",
          data:{
          'split_location':split_location,
          'csrfmiddlewaretoken':$('input[name="csrfmiddlewaretoken"]').val()
          },
            success: function (response) {  
              $('#msg').empty();   
              $('#LocModalBody').empty();
              $('#LocModalBody').append(response);
              $('#shift_id').val(split_location);
         

            },
            error: function (err) {
              console.log(err)
            } 
        });
  });
});
// .........................................................................................................................................................


// GET ROOM...................................................................................................................................................
$(function() {
  $('.select-room').change(function(){
    store_room = $(this).val();
    split_room = store_room.split('room-')[1];
    

    $('.option2').hide();
    $('#' + $(this).val()).show();
  
      $.ajax({
        type: 'get',
        url: '/administration/planner/',
        contentType: "application/json",
        data:{
        'split_room':split_room,
        'csrfmiddlewaretoken':$('input[name="csrfmiddlewaretoken"]').val()
        },
        success: function (response) {
          $('#roommsg').empty(); 
          $('#RoomModalBody').empty();
          $('#RoomModalBody').append(response);
          $('#edit_room_id').val(split_room);
          
            
        },
      });
  });
});








// $(function() {
//   $('.renew-type').change(function(){
//     // if($(this).val()=="email"){

//     // }
//     // else
//     // {

//     // }
//       $('.renew-option').hide();
//       $('#' + $(this).val()).show();
//   });
// }); 

//12th August 2019
// $(document).ready(function(){
//   $(".btn-collaps").click(function() {
//     console.log($(this).text())
//     if($(this).text() == "Expand"){
//       $(this).text("Collapse");
//     }
//     else{
//       $(this).text("Expand");
//     }
//   });
// });