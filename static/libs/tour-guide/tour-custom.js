var tour, tourSteps;

$(function() {
    var dashboardUrl = window.location.href === window.location.origin + "/administration/dashboard/" ? "" : window.location.origin + "/administration/dashboard/"
    //var checkinPageUrl = window.location.href === window.location.origin + "/administration/checkin/" ? "" : window.location.origin + "/administration/checkin/"
    var customersPageUrl = window.location.href === window.location.origin + "/administration/customers/" ? "" : window.location.origin + "/administration/customers/"
    var storePageUrl = window.location.href === window.location.origin + "/store/servicepass/" ? "" : window.location.origin + "/store/servicepass/"
    var schedulePageUrl = window.location.href === window.location.origin + "/administration/schedule/" ? "" : window.location.origin + "/administration/schedule/"
    var staffPageUrl = window.location.href === window.location.origin + "/administration/staff/" ? "" : window.location.origin + "/administration/staff/"
    var storePageUrl = window.location.href === window.location.origin + "/store/servicepass/" ? "" : window.location.origin + "/store/servicepass/"
    var plannerPageUrl = window.location.href === window.location.origin + "/administration/planner/" ? "" : window.location.origin + "/administration/planner/"
    var permissionsPageUrl = window.location.href === window.location.origin + "/administration/permissions/" ? "" : window.location.origin + "/administration/permissions/"
    var tourSteps = [
        {
            path: dashboardUrl,
            /*orphan: true,*/
            element: "#dashboard-content",
            placement: "bottom",
            title: gettext("Homepage"),
            content: gettext("A look at the next 24-hours displayed on one dashboard!<br> See all your scheduled services and compare your customer traffic between today and yesterday. Check out who’s on staff today and when they’re scheduled to be in, leave a note for your team and a get things done with your team to-do list.")
        },
        {
            path: dashboardUrl,
            element: "#item-img-output",
            placement: "bottom",
            title: gettext("Logo"),
            content: gettext("Upload your business logo here")
        },
        /*{
          path: checkinPageUrl,
          element: "#checkin-page",
          placement: "bottom",
          title: gettext("Check-In"),
          content: gettext("Use this page to check-in customers for services. Go to Schedule to populate this calendar.")
        },*/
        {
          path: customersPageUrl,
          element: "#customers-page",
          placement: "bottom",
          title: gettext("Customers"),
          content: gettext("Access data for your customers here, and make changes to their accounts.")
        },
        {
          path: storePageUrl,
          element: "#store-page",
          placement: "bottom",
          title: gettext("Store"),
          content: gettext("Sell items to in-person customers, and add items to your store such as service packs, merchandise, and gift cards.")
        },
        {
          path: schedulePageUrl,
          element: "#schedule-page",
          placement: "bottom",
          title: gettext("Schedule"),
          content: gettext("Use this familiar calendar view to add services to your calendar. First, create a new service type. Next, click Add Service to populate service details and add to the calendar.")
        },
        {
          path: staffPageUrl,
          element: "#staff-page",
          placement: "bottom",
          title: gettext("Staff"),
          content: gettext("Manage your staff's shifts, tasks, and swap requests.")
        },
//        {
//          path: storePageUrl,
//          element: "#inventory-page",
//          placement: "bottom",
//          title: gettext("Inventory"),
//          content: gettext("Keep track of your inventory and all vendor details on this page.")
//        },
        {
          path: plannerPageUrl,
          element: "#ruoom-planner-page",
          placement: "bottom",
          title: gettext("Ruoom Planner"),
          content: gettext("Configure all your rooms and business settings here. Need to figure out how many customers can fit in a space? Our patent-pending optimisation algorithm will calculate that for you.")
        }//,
//        {
//          path: permissionsPageUrl,
//          element: "#permissions-page",
//          placement: "bottom",
//          title: gettext("Permissions"),
//          content: gettext("Grant or edit platform access to your service providers and staff.")
//        },
//        {
//          path: permissionsPageUrl,
//          element: "#report-error",
//          placement: "bottom",
//          title: gettext("Report Error"),
//          content: gettext("Is something not working right? Report any bugs or errors you encounter, and our staff will promptly attend to it.")
//        }
    ];

    tour = new Tour({
        framework: "bootstrap4",
        name: "tour",
        steps: tourSteps,
        storage: window.localStorage,
        debug: true,
        backdrop: true
    });

    $("#btnStart").on("click", function()
    {
        // Use .restart to always start the tour. Normally you'd use tour.start(), and perhaps onPreviouslyEnded.
        tour.restart();
    });

});
