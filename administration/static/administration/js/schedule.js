var calendarTableStyles = {
  border: tableGridThickness + " solid " + tableBorderColor
};

function applyBorderStyles() {
  $(".fc-day").css(calendarTableStyles);
  $(".fc-day-header").css(calendarTableStyles);
  $(".fc-widget-content").css(calendarTableStyles);
  $(".fc-head-container").css(calendarTableStyles);
}

$(document).ready(function() {

  var calendarDiv = document.getElementById("id_calendar");

  showAllDayBar = false
  var events_list = []   // List of events to be rendered on the calendar
  if (booking_plugin) {
    events_list = events_list.concat(list_services());
  }
  
  var calendar = new FullCalendar.Calendar(calendarDiv, {
    plugins: ["dayGrid", "timeGrid", "interaction"],
    defaultView: "dayGridMonth",
    eventColor: classBlockColor,
    eventTextColor: classTextColor,
    height: 655,
    locale: window.lang,
    droppable: true,
    editable: true,
    header: {
      left: "prev,next",
      center: "title",
      right: "timeGridDay,timeGridWeek,dayGridMonth"
    },
    events: events_list,
    eventSources: [
      function(fetchInfo, successCallback, failureCallback) {
        try {
          $.ajax({
            url: "/administration/schedule/google-events",
            method: "GET",
            data: {
              start: fetchInfo.start.toISOString(),
              end: fetchInfo.end.toISOString(),
              tz: (typeof locationTimezone !== 'undefined' && locationTimezone) ? locationTimezone : Intl.DateTimeFormat().resolvedOptions().timeZone
            },
            success: function(data) { successCallback(data || []); },
            error: function() { failureCallback(); }
          });
        } catch (e) {
          failureCallback(e);
        }
      }
    ],
    eventRender: function(eventInfo) {
      if (booking_plugin) {
        render_service(eventInfo);
      }
    },
    dateClick: (dateInfo) => {
      // Load date object
      let selectedDate = dateInfo.date;

      // Open dialog
      $(".card-header>.row>div>button:last-child").click()

      // Load flatpickr instance
      let instance = $("label[for=id_scheduled_time] + input#id_scheduled_time")[0]._flatpickr

      // Set date to new date
      instance.setDate(selectedDate, true);
    },
    eventDrop: (dragInfo) => {
      // Only update if user confirm
      
      // Update and reload
      let token = $("[name=csrfmiddlewaretoken]").val()
      $.ajax({
        url: "/administration/schedule/",
        method: "POST",
        processData: false,
        contentType: "application/x-www-form-urlencoded",
        data: (
          "update_class=true&"
          + `csrfmiddlewaretoken=${encodeURIComponent(token)}&`
          + `id=${encodeURIComponent(dragInfo.event.id)}&`
          + `scheduled_time=${encodeURIComponent(dragInfo.event.start.toString())}`
        ),
        success: (response) => {
          window.location.reload();
        },
        error: function(err) {
          dragInfo.revert();
        }
      });
    }
  });

  calendar.render();

  var allRows = $("div.fc-slats tr");
  var index = 0,
    startTimeFound = false,
    endTimeFound = false;
  for (index = 0; index < allRows.length; index++) {
    if (!startTimeFound) {
      if ($(allRows[index]).text() === gettext(businessHours.startTime)) {
        startTimeFound = true;
        continue;
      }
      $(allRows[index]).css("background-color", "lightgray");
    } else {
      if ($(allRows[index]).text() === gettext(businessHours.endTime)) {
        endTimeFound = true;
        continue;
      }
    }
    if (!startTimeFound || (startTimeFound && endTimeFound)) {
      $(allRows[index]).css("background-color", "lightgray");
    }
  }

  $("#id_duration").mask("00:00");

  // default WeekView
  applyBorderStyles();
  var activeView = "week";
  // when clicked: MonthView
  $(".fc-dayGridMonth-button").click(function() {
    if (activeView !== "month") {
      applyBorderStyles();
      activeView = "month";
    }
  });
  // when clicked: weekView
  $(".fc-timeGridWeek-button").click(function() {
    if (activeView !== "week") {
      applyBorderStyles();
      activeView = "week";
    }
  });
  // When clicked dayView
  $(".fc-timeGridDay-button").click(function() {
    if (activeView !== "day") {
      applyBorderStyles();
      activeView = "day";
    }
  });

  //Apply business hours
  $(".fc-button").click(function() {
    
    var allRows = $("div.fc-slats tr");
    var index = 0,
      startTimeFound = false,
      endTimeFound = false;
    for (index = 0; index < allRows.length; index++) {
      if (!startTimeFound) {
        if ($(allRows[index]).text() === gettext(businessHours.startTime)) {
          startTimeFound = true;
          continue;
        }
        $(allRows[index]).css("background-color", "lightgray");
      } else {
        if ($(allRows[index]).text() === gettext(businessHours.endTime)) {
          endTimeFound = true;
          continue;
        }
      }
      if (!startTimeFound || (startTimeFound && endTimeFound)) {
        $(allRows[index]).css("background-color", "lightgray");
      }
    }
  });
  
  $("form").submit(function(event) {
    try {
      if ($("#" + event.target.id + " input.is-invalid").length) {
        event.preventDefault();
        alert(gettext("Please resolve errors before submitting the form"));
      }
    } catch(err) {
      return
    }
  });

  function getDurationAndAddField(formSelector) {
    var minutes = $(formSelector + " #id_duration_mins").val();
    if (!minutes) {   //Default minutes to zero
      minutes=0;
    }
    var hours = $(formSelector + " #id_duration_hours").val();
    if (!hours) {   //Default hours to zero
      hours=0;
    }
    var days = $(formSelector + " #id_duration_days").val();
    if (!days) {   //Default days to zero
      days=0;
    }
    if (!(minutes | hours | days)) {  //return if there is no data
      return
    }

    var durationValue =
      days + ":" + hours + ":" + minutes;
    $("<input />")
      .attr("id", "id_duration")
      .attr("name", "duration")
      .attr("value", durationValue)
      .attr("type", "hidden")
      .appendTo("form" + formSelector);
    return true;
  }

  $("#searchcustomer").autocomplete("option", "appendTo", "#searchResult");

  $("#searchprofile").autocomplete({
    source: "/administration/profile/search/",
    minLength: 1,
    open: function() {
      setTimeout(function() {
        $(".ui-autocomplete").css("z-index", 99);
      }, 0);
    },
    select: function(event, ui) {
      $("#searchprofile").blur();
      //Logic after searching for customer here
    }
  });

  $("#searchprofile").autocomplete("option", "appendTo", "#searchResult");

  $("#searchcustomer").focus(function() {
    $("#searchcustomer").val("");
    $("#registrationStatusMessage").hide();
    $("#registrationStatusMessage").removeClass();
  });

  $("#searchprofile").focus(function() {
    $("#searchprofile").val("");
    $("#registrationStatusMessage").hide();
    $("#registrationStatusMessage").removeClass();
  });
});