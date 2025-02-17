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
      $("#update-row-02").removeClass("display-none");
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
    $(".btn-collaps").click(function() {
        if($(this).text() == "Expand"){
        $(this).text("Collapse");
        }
        else{
        $(this).text("Expand");
        }
    });
});
