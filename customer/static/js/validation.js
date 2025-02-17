  $(document).ready(function() {
    $("#amount_id").keyup(function() {
        $(this).val($(this).val().replace(/[^0-9]/g, ''));
    });
  });
