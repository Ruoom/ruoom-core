$(document).ready(function () {

    $('#p_id').hide();
    

    $(document).on("click", ".deleteUserButton", function () {
        let user_id = $(this).attr('data-id');
        $("#delete_confirmation_modal #staff_id").val(user_id);
    });

    function resetEditForm() {
       
      $('form#userEditForm input[name=first_name]').val('');
      $('form#userEditForm input[name=last_name]').val('');
      $('form#userEditForm input[name=email]').val('');
      $('form#userEditForm input[name=is_teacher]').prop('checked', false);
      $('form#userEditForm input[name=is_superuser]').prop('checked', false);

      // Checkbox
      $('form#userEditForm input[name=message_consent]').prop('checked', false);
      $('form#userEditForm input[name=staff_is_active]').prop('checked', false);
      
      let permissions = $('form#userEditForm input:checkbox[name=Permissions]');
      permissions.each((index, permissionBox) => {
          permissionBox.checked = false;
      });
    }


    $('#create_Form').on('submit', function (e) {
        get_email = $('#id_email').val()
     
        var regex = /^([a-zA-Z0-9_\.\-\+])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
        if(!regex.test(get_email)) {
            e.preventDefault();
            $("#p_id").show();
          
        }else{
            $("#p_id").hide();
        
      
        }
    });


    $(document).on("click", ".editUserButton", function () {
        let user_id = $(this).attr('data-id');
        $.ajax({
            url: '/administration/permissions',
            data: {
                staff_id: user_id,
                TYPE: 'get_staff_data'
            },
            method: 'GET',
            success: function (data) {
            console.log(data)
                resetEditForm();
              
                $('#user_id').val(user_id);
                $('form#userEditForm input[name=is_superuser]').change(handleSuperUserPermissionsChange);
                $('form#userEditForm input:checkbox[name=Permissions]').change(handlePagePermissionChange);
                $('form#userEditForm input[name=first_name]').val($('input[name=first_name]', data).val())
                $('form#userEditForm input[name=last_name]').val($('input[name=last_name]', data).val())
                $('form#userEditForm input[name=email]').val($('input[name=email]', data).val())
                $('form#userEditForm input[name=is_teacher]').prop('checked', $('input[name=is_teacher]', data).prop('checked'));

                // Checkbox
                $('form#userEditForm input[name=message_consent]').prop('checked', $('input[name=message_consent]', data).prop('checked'));
                $('form#userEditForm input[name=staff_is_active]').prop('checked', $('input[name=staff_is_active]', data).prop('checked'));

                if ($('input[name=is_superuser]', data).prop('checked') && $('form#userEditForm input[name=is_superuser]').prop('checked') == false) {
                  $('form#userEditForm input[name=is_superuser]').click();
                }
                $('#modalUserEditModal').modal('show');
                },
            error: function (err) {
                console.log(err)
            }
        });
    });

    $(document).on("click", ".resetPasswordButton", function () {
        reset_username = $(this).attr('reset-username');
        reset_id = $(this).attr('reset-id');
        document.getElementById("reset-username").innerHTML = reset_username
        document.getElementById("reset-id").setAttribute("value", reset_id)
        $("#reset_password_modal #id_email").val(reset_username);
     
    });

    // $(document).on("click", ".deleteUserButton", function () {
    //     reset_username = $(this).attr('data-id');
    //     document.getElementById("remove-username").innerHTML = reset_username
    // });

    $('#userEditForm').on('submit', function (event) {
        
      
        var post_url = $(this).attr("action"); //get form action url
        
        var request_method = $(this).attr("method"); //get form GET/POST method
        
        var form_data = $(this).serialize(); //Encode form elements for submission
    
        
        $('#msg').html('');
     
        $.ajax({
            url: post_url,
            type: request_method,
            data: form_data,
            success: function (response) {
               
                if (response['status'] === 'updated') {
                    
                    $('#msg').append(
                        '<div class="alert alert-success">'
                        + '<strong>Updated!</strong> User Updated.'
                        + '</div>'
                    );
                    location.reload(true);
                    updateUserInTable();
                }
                
                else if (response['status'] === 'form_error') {
                  
                  const errors = response['errors'];
                  Object.keys(errors).forEach(key => {
                    let currentKeyErrors = errors[key].map(err=>`${key}: ${err}`);
                    $('#msg').append(
                        '<div class="alert alert-danger"><strong>Error! </strong>' + currentKeyErrors + '</div>'
                    );
                  });
                }
            },
                
            error: function (err) {
                console.log(err);
            }

        });
    });

    $('input[name=is_superuser]').change(handleSuperUserPermissionsChange);
    $('input[name=Permissions]').change(handlePagePermissionChange);

    if (showCreateUserForm) {
        $('#modalUserForm').modal('show');
    }

    if (showEditUserForm) {
      $('#modalUserEditModal').modal('show');
    }

});

function handleSuperUserPermissionsChange(event) {
    let permissionsSelectors;
    if (this.form.id === 'userEditForm') {
        permissionsSelectors = 'form#userEditForm input:checkbox[name=Permissions]';
    } else {
        permissionsSelectors = 'form:not(#userEditForm) input:checkbox[name=Permissions]';
    }
    let permissions = $(permissionsSelectors);
    permissions.each((index, permissionBox) => {
        permissionBox.checked = this.checked;
    });

}

function handlePagePermissionChange(event) {
    let superuser_check_selector;
    if (this.form.id === 'userEditForm') {
        superuser_check_selector = 'form#userEditForm input:checkbox[name=is_superuser]';
    } else {
        superuser_check_selector = 'form:not(#userEditForm) input:checkbox[name=is_superuser]';
    }
    if (this.checked === false) {
        $(superuser_check_selector)[0].checked = false;
    }
}

function updateUserInTable() {
    let user_id = $('#userEditForm #user_id').val();
    let first_name = $('#userEditForm #id_first_name').val();
    let last_name = $('#userEditForm #id_last_name').val();
    let superuser = $('#userEditForm #id_is_superuser').is(':checked');
    let is_service_provider = $('#userEditForm input[name=is_teacher]').prop('checked') == true;

    // Checkbox
    let message_consent_provider = $('#userEditForm input[name=message_consent]').prop('checked') == true;

    // permission checkbox 
    let check_permission = $('#userEditForm input[name=Permissions]').prop('checked') == true;
    let isActive = $('#userEditForm input[name=staff_is_active]').prop('checked') == true;

    var img = $('#table_row_' + user_id + ' td.text-left').find('img').prop('outerHTML');
    $('#table_row_' + user_id).find('td')[0].innerHTML = img + first_name + ' ' + last_name;
    if (superuser) {
        $('#table_row_' + user_id).find('td')[1].innerHTML = 'Yes';
    } else {
        $('#table_row_' + user_id).find('td')[1].innerHTML = 'No';
    }

    if (is_service_provider) {
      $('#table_row_' + user_id).find('td')[2].innerHTML = 'Yes';
    } else {
        $('#table_row_' + user_id).find('td')[2].innerHTML = 'No';
    }

    // Checkbox
    if (message_consent_provider) {
        $('#table_row_' + user_id).find('td')[2].innerHTML = 'Yes';
      } else {
          $('#table_row_' + user_id).find('td')[2].innerHTML = 'No';
      }

    //   Permission Checkbox

    if (check_permission) {
        $('#table_row_' + user_id).find('td')[2].innerHTML = 'Yes';
      } else {
          $('#table_row_' + user_id).find('td')[2].innerHTML = 'No';
      }

    if (isActive) {
      $('#table_row_' + user_id).find('td')[3].innerHTML = 'Yes';
    }
    else {
      $('#table_row_' + user_id).find('td')[3].innerHTML = 'No';
    }

}

