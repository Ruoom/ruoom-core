var closebtns = document.getElementsByClassName("badge_close");
var i;


for (i = 0; i < closebtns.length; i++) {
  closebtns[i].addEventListener("click", function() {
    this.parentElement.style.display = 'none';
  });
}

function uploadFile(file, action){
  var xhr = new XMLHttpRequest();
  xhr.open("POST", document.location.origin + action);

  var postData = new FormData();
  postData.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value)
  postData.append("file", file);

  xhr.onreadystatechange = function() {
    if(xhr.readyState === 4){
      if (xhr.status === 200 || xhr.status === 204){
        console.log("Image uploaded to " + action + " succesfully.")
        window.location.reload()
      }
      else{
        console.log("Could not upload file to " + action + ".");
        $('#item-img-output').removeClass('spinner-border')
      }
   }
  };
  xhr.send(postData);
}

function addMinutes(date, minutes) {
    return new Date(date.getTime() + minutes*60000);
}

// $(function() {
//   $('.how-to-send').change(function(){
//     // if($(this).val()=="email"){

//     // }
//     // else
//     // {

//     // }
//       $('.option').hide();
//       $('#' + $(this).val()).show();
//   });
// }); 


// $(function() {
//   $('.service-type').change(function(){
//     // if($(this).val()=="email"){

//     // }
//     // else
//     // {

//     // }
//       $('.option-limited').hide();
//       $('#' + $(this).val()).show();
//   });
// }); 


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
function showModel(timeout, modelTitle, modelBodyText){
  if(modelTitle != undefined){
    $("#formSuccessModel #modelTitle").text(modelTitle);  
  }
  if(modelBodyText != undefined){
    $("#formSuccessModel #modelBodyText").text(modelBodyText);  
  }
  $('#formSuccessModel').modal('show');
  if(timeout != undefined){
    setTimeout(function () {
        $("#formSuccessModel").modal('hide');
    }, 1000); 
  }else{
    setTimeout(function () {
        $("#formSuccessModel").modal('hide');
    }, 1000); 
  }
}
function removeParams(sParam)
{
  var url = window.location.href.split('?')[0]+'?';
  var sPageURL = decodeURIComponent(window.location.search.substring(1));
  var sURLVariables = sPageURL.split('&amp;');
  var sParameterName,i;

  for (i = 0; i<sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');
      if (sParameterName[0] != sParam) {
          url = url + sParameterName[0] + '=' + sParameterName[1] + '&amp;'
      }
  }
  return url.substring(0,url.length-1);
}

