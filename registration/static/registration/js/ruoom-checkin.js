var closebtns = document.getElementsByClassName("badge_close");
var i;

for (i = 0; i < closebtns.length; i++) {
  closebtns[i].addEventListener("click", function() {
    this.parentElement.style.display = 'none';
  });
}


$(function() {
  $('.how-to-send').change(function(){
    // if($(this).val()=="email"){

    // }
    // else
    // {

    // }
      $('.option').hide();
      $('#' + $(this).val()).show();
  });
}); 


$(function() {
  $('.service-type').change(function(){
    // if($(this).val()=="email"){

    // }
    // else
    // {

    // }
      $('.option-limited').hide();
      $('#' + $(this).val()).show();
  });
}); 


$(function() {
  $('.select-location').change(function(){
    // if($(this).val()=="email"){

    // }
    // else
    // {

    // }
      $('.option1').hide();
      $('#' + $(this).val()).show();
  });
}); 

$(function() {
  $('.select-room').change(function(){
    // if($(this).val()=="email"){

    // }
    // else
    // {

    // }
      $('.option2').hide();
      $('#' + $(this).val()).show();
  });
}); 

$(function() {
  $('.renew-type').change(function(){
    // if($(this).val()=="email"){

    // }
    // else
    // {

    // }
      $('.renew-option').hide();
      $('#' + $(this).val()).show();
  });
}); 


$(document).ready(function(){

  $("#update01").click(function(){
    $("#update-row-01").addClass("display-none");
    $("#update-show-01").addClass("display-show");
  });
  
  $("#edit-show-01").click(function(){
    $("#update-row-01").removeClass("display-none");
    $("#update-show-01").removeClass("display-show");
  });

  $("#update02").click(function(){
    $(".update-row-02").addClass("display-none");
    $("#update-show-02").addClass("display-show");
  });
  
  $("#edit-show-02").click(function(){
    $(".update-row-02").removeClass("display-none");
    $("#update-show-02").removeClass("display-show");
  });

  $("#update03").click(function(){
    $("#update-row-03").addClass("display-none");
    $("#update-show-03").addClass("display-show");
  });
  
  $("#edit-show-03").click(function(){
    $("#update-row-03").removeClass("display-none");
    $("#update-show-03").removeClass("display-show");
  });

  $("#update04").click(function(){
    $("#update-row-04").addClass("display-none");
    $("#update-show-04").addClass("display-show");
  });
  
  $("#edit-show-04").click(function(){
    $("#update-row-04").removeClass("display-none");
    $("#update-show-04").removeClass("display-show");
  });

  
  $("#auth-update01").click(function(){
    $("#auth-update-row-01").addClass("display-none");
    $("#auth-update-show-01").addClass("display-show");
    $(".shared-account-card").addClass("display-show");
  });
  
  $("#auth-re-update01").click(function(){
    $("#auth-update-row-01").removeClass("display-none");
    $("#auth-update-show-01").removeClass("display-show");

  });


  $("#account-show-01").click(function(){
    $("#show-date-acc-status").addClass("display-none");
    $("#edit-date-acc-status").addClass("display-show");
  });
  
  $("#account-show-back").click(function(){
    $("#show-date-acc-status").removeClass("display-none");
    $("#edit-date-acc-status").removeClass("display-show");

  });
  
  $('#checkbox1').change(function () {
    if($('#checkbox1').is(":checked"))   {
      $(".span-show-default").addClass("display-none");
      $(".span-show-view").addClass("display-show");
      $(".body-rows-card").addClass("display-show");
      $("#shared-hr-row1").addClass("display-show");
    }
    else{
      $(".span-show-default").removeClass("display-none");
      $(".span-show-view").removeClass("display-show");
      $(".body-rows-card").removeClass("display-show");
      $("#shared-hr-row1").removeClass("display-show");
    }
        
  });


  $(".form-radio").click(function () {
    if ($(this).is(":checked")) {
      $(".form-radio").parent().parent().removeClass("active");
      $(this).parent().parent().addClass("active");
    }
    else{

    }
});
 


$("#form-radio3").click(function () {
  if ($(this).is(":checked")) {
    $(".card-saved").css("display", "none");
    $(".cash-accepted").css("display", "block");
    $(".complimentory").css("display", "none");
    $(".comp-1").css("text-decoration", "none");
    $(".comp-2").css("display", "none");
  }
});

$("#form-radio2").click(function () {
  if ($(this).is(":checked")) {
    $(".card-saved").css("display", "none");
    $(".complimentory").css("display", "block");
    $(".cash-accepted").css("display", "none");
    $(".comp-1").css("text-decoration", "line-through");
    $(".comp-2").css("display", "inline-block");
  }
});

$("#form-radio1").click(function () {
  if ($(this).is(":checked")) {
    $(".card-saved").css("display", "block");
    $(".cash-accepted").css("display", "none");
    $(".complimentory").css("display", "none");
    $(".comp-1").css("text-decoration", "none");
    $(".comp-2").css("display", "none");
  }
});



  $(".btn-collaps").click(function() {
  console.log($(this).text())
  if($(this).text() == "Expand"){
    $(this).text("Collapse");
  }
  else{
    $(this).text("Expand");
  }

  

  });



});



$(document).ready(function() {
  $('#paynow').prop('disabled', true);
  $('#cardnumber').keyup(function() {
     if($(this).val() > 0) {
        $('#paynow').prop('disabled', false);
     }
     else
     {
      $('#paynow').prop('disabled', true);
     }
  });
});


