var calendarTableStyles = {
    border: tableGridThickness + ' solid ' + tableBorderColor
}


function applyBorderStyles() {
    $('.fc-day').css(calendarTableStyles);
    $('.fc-day-header').css(calendarTableStyles);
    $('.fc-widget-content').css(calendarTableStyles);Ch
    $('.fc-head-container').css(calendarTableStyles);
}

function displayCheckinButto    n(classId) {
    return `
    <a href="/administration/checkin/${classId}"> <span class="btn btn-primary">Check In</span><a>
    `;
}

$(document).ready(function () {
    if ($.find('#id_scheduled_time').length) {
        $('#id_scheduled_time')[0].flatpickr({
            enableTime: true,
            dateFormat: "Y-m-d H:i",
        })
    }

    var calendarDiv = document.getElementById('id_calendar');

    var classes_list = classes.map(function (value, index, classes) {
        start_date = new Date(value.scheduled_time);
        end_date = new Date(value.scheduled_time);
        classDuration = value.duration;
        classHours = Number(classDuration.split(':')[0])
        classMinutes = Number(classDuration.split(':')[1])
        end_date.setHours(start_date.getHours() + classHours)
        end_date.setMinutes(start_date.getMinutes() + classMinutes)
        return {
            title: value.class_type.name,
            classId: value.id,
            start: start_date,
            end: end_date,
            teacher: value.teacher,
            duration: value.duration,
            class_occured: value.class_occured,
        }
    })


    var calendar = new FullCalendar.Calendar(calendarDiv, {
        plugins: ['dayGrid', 'timeGrid'],
        defaultView: 'timeGridWeek',
        eventColor: classBlockColor,
        eventTextColor: classTextColor,
        height: 655,
        header: {
            left: 'prev,next',
            center: 'title',
            right: 'today,timeGridDay,dayGridMonth,timeGridWeek'
        },
        events: classes_list,
        allDaySlot: showAllDayBar ? true : false,
        scrollTime: "9:00:00",
        businessHours: businessHours,
        eventClick: function (eventInfo) {
            $('.activeEvent').css('background-color', classBlockColor);
            $('.activeEvent').removeClass('activeEvent');
            $(eventInfo.el).addClass('activeEvent');
            $(eventInfo.el).css('background-color', highlightedClassColor)

            $('#modalClassDetails .class-title').html(eventInfo.event.title);
            $('#modalClassDetails #class-teacher').val(eventInfo.event.extendedProps.teacher);
            $('#modalClassDetails #class-start').val(eventInfo.event.start);
            $('#modalClassDetails #class-end').val(eventInfo.event.end);
            if (eventInfo.event.extendedProps.class_occured === 'True') {
                $('#modalClassDetails #classCheckinButton').html(displayCheckinButton(eventInfo.event.extendedProps.classId));
            } else {
                $('#modalClassDetails #classCheckinButton').html('');
            }

        },
        eventRender: function(eventInfo) {
            eventInfo.el.dataset['toggle'] = 'modal';
            eventInfo.el.dataset['target'] = '#modalClassDetails';
            $(eventInfo.el).find('.fc-title').append("<br/>" + eventInfo.event.extendedProps.teacher);
        }
    });

    calendar.render();


    $('#id_duration').mask('00:00');

    // default WeekView
    applyBorderStyles();
    var activeView = 'week';
    // when clicked: MonthView
    $('.fc-dayGridMonth-button').click(function () {
        if (activeView !== 'month') {
            applyBorderStyles();
            activeView = 'month';
        }
    })
    // when clicked: weekView
    $('.fc-timeGridWeek-button').click(function () {
        if (activeView !== 'week') {
            applyBorderStyles();
            activeView = 'week';
        }
    })
    // When clicked dayView
    $('.fc-timeGridDay-button').click(function () {
        if (activeView !== 'day') {
            applyBorderStyles();
            activeView = 'day';
        }
    })



    $('input').change(function (event) {
        if (event.target.value === '') {
            $(event.target).hasClass('is-valid') ? event.target.classList.remove('is-valid') : null;
            !$(event.target).hasClass('is-invalid') ? event.target.classList.add('is-invalid') : null;

        } else if (event.target.id === 'id_level' && event.target.value < 0) {
            $(event.target).hasClass('is-valid') ? event.target.classList.remove('is-valid') : null;
            !$(event.target).hasClass('is-invalid') ? event.target.classList.add('is-invalid') : null;
            $('<span class="invalid-feedback">Level cannot be negative</span>').insertAfter('#id_level');

        } else {
            $(event.target).hasClass('is-invalid') ? event.target.classList.remove('is-invalid') : null;
            !$(event.target).hasClass('is-valid') ? event.target.classList.add('is-valid') : null;

        }
    })

    $('form').submit(function (event) {
        if ($('#' + event.target.id + ' input.is-invalid').length) {
            event.preventDefault();
            alert('Please resolve errors before submitting the form');
        }
    })
})
