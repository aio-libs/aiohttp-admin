/*global angular*/

/*
 * This is an example ng-admin configuration for a blog administration composed
 * of three entities: post, comment, and tag. Reading the code and the comments
 * will help you understand how a typical ng-admin application works. You can
 * browse the result online at http://ng-admin.marmelab.com.
 *
 * The remote REST API is simulated in the browser, using FakeRest
 * (https://github.com/marmelab/FakeRest). Look at the JSON responses in the
 * browser console to see the data used by ng-admin.
 *
 * For simplicity's sake, the entire configuration is written in a single file,
 * but in a real world situation, you would probably split that configuration
 * into one file per entity. For another example configuration on a larger set
 * of entities, and using the best development practices, check out the
 * Posters Galore demo (http://marmelab.com/ng-admin-demo/).
 */
(function () {
    "use strict";

    var app = angular.module('aiohttp_admin', ['ng-admin']);

    // Admin definition
    app.config(['NgAdminConfigurationProvider', function (NgAdminConfigurationProvider) {
        var nga = NgAdminConfigurationProvider;

        function truncate(value) {
            if (!value) {
                return '';
            }

            return value.length > 50 ? value.substr(0, 50) + '...' : value;
        }

        var admin = nga.application('ng-admin backend demo') // application main title
            .debug(true) // debug disabled
            .baseApiUrl('/admin/'); // main API endpoint

        // define all entities at the top to allow references between them
        {% for entity in entities %}
            var {{ entity.name }} = nga.entity('{{ entity.url }}');
        {% endfor %}

        // set the application entities
        admin
        {% for entity in entities %}.addEntity({{ entity.name }}){% endfor %};

        // customize header
        var customHeaderTemplate =
        '<div class="navbar-header">' +
            '<button type="button" class="navbar-toggle" ng-click="isCollapsed = !isCollapsed">' +
              '<span class="icon-bar"></span>' +
              '<span class="icon-bar"></span>' +
              '<span class="icon-bar"></span>' +
            '</button>' +
            '<a class="navbar-brand" href="#" ng-click="appController.displayHome()">{{ name }}</a>' +
        '</div>';
        admin.header(customHeaderTemplate);

        // customize menu
        admin.menu(nga.menu()
            {% for entity in entities %}
                .addChild(nga.menu({{ entity.name }}).title('{{ entity.name | capitalize }}').icon(''))
            {% endfor %}
        );

        // customize entities and views
        {% for entity in entities %}

            // list view
            {{ entity.name }}.listView()
                .title('{{ entity.name | capitalize }}') // default title is "[Entity_name] list"
                .description('List of {{ entity.name }} with infinite pagination') // description appears under the title
                .infinitePagination(true) // load pages as the user scrolls
                .fields([
                    {% for title, type in entity.columns %}
                        nga.field('{{ title }}', '{{ type }}'),
                    {% endfor %}
                ])
                .listActions(['show', 'edit', 'delete']);

            // creation view
            {{ entity.name }}.creationView()
                .fields([
                    {% for title, type in entity.columns %}
                        nga.field('{{ title }}', '{{ type }}'),
                    {% endfor %}
                ]);

            // edition view
            {{ entity.name }}.editionView()
                .title('Edit {{ entity.name }} {{"{{ entry.values.title }}"}}') // title() accepts a template string, which has access to the entry
                .actions(['list', 'show', 'delete']) // choose which buttons appear in the top action bar. Show is disabled by default
                .fields([
                    {% for title, type in entity.columns %}
                        nga.field('{{ title }}', '{{ type }}'),
                    {% endfor %}
                ]);

            // show view
            {{ entity.name }}.showView() // a showView displays one entry in full page - allows to display more data than in a a list
                .fields([
                    {% for title, type in entity.columns %}
                        nga.field('{{ title }}', '{{ type }}'),
                    {% endfor %}
                ]);

            // deletion view
            {{ entity.name }}.deletionView()
                .title('Deletion confirmation'); // customize the deletion confirmation message

        {% endfor %}

        // customize dashboard
        var customDashboardTemplate =
        '<div class="row dashboard-starter"></div>' +
            {% for entity in entities %}
                '<div class="row dashboard-content">' +
                    '<div class="col-lg-12">' +
                        '<div class="panel panel-default">' +
                            '<ma-dashboard-panel collection="dashboardController.collections.{{ entity.url }}" entries="dashboardController.entries.{{ entity.url }}" datastore="dashboardController.datastore"></ma-dashboard-panel>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
            {% endfor %}
         '<div class="row dashboard-content"></div>';

        admin.dashboard(nga.dashboard()
            {% for entity in entities %}
                .addCollection(nga.collection({{ entity.name }})
                    .title('{{ entity.name | capitalize }}')
                )
            {% endfor %}
            .template(customDashboardTemplate)
        );

        nga.configure(admin);
    }]);


    app.directive('postLink', ['$location', function ($location) {
        return {
            restrict: 'E',
            scope: { entry: '&' },
            template: '<p class="form-control-static"><a ng-click="displayPost()">View&nbsp;post</a></p>',
            link: function (scope) {
                scope.displayPost = function () {
                    $location.path('/posts/show/' + scope.entry().values.post_id); // jshint ignore:line
                };
            }
        };
    }]);

    app.directive('sendEmail', ['$location', function ($location) {
        return {
            restrict: 'E',
            scope: { post: '&' },
            template: '<a class="btn btn-default" ng-click="send()">Send post by email</a>',
            link: function (scope) {
                scope.send = function () {
                    $location.path('/sendPost/' + scope.post().values.id);
                };
            }
        };
    }]);

    // custom 'send post by email' page

    function sendPostController($stateParams, notification) {
        this.postId = $stateParams.id;
        // notification is the service used to display notifications on the top of the screen
        this.notification = notification;
    }
    sendPostController.prototype.sendEmail = function() {
        if (this.email) {
            this.notification.log('Email successfully sent to ' + this.email, {addnCls: 'humane-flatty-success'});
        } else {
            this.notification.log('Email is undefined', {addnCls: 'humane-flatty-error'});
        }
    };
    sendPostController.$inject = ['$stateParams', 'notification'];

    var sendPostControllerTemplate =
        '<div class="row"><div class="col-lg-12">' +
            '<ma-view-actions><ma-back-button></ma-back-button></ma-view-actions>' +
            '<div class="page-header">' +
                '<h1>{{ "Send post #{{ controller.postId }} by email" }}</h1>' +
                '<p class="lead">You can add custom pages, too</p>' +
            '</div>' +
        '</div></div>' +
        '<div class="row">' +
            '<div class="col-lg-5"><input type="text" size="10" ng-model="controller.email" class="form-control" placeholder="name@example.com"/></div>' +
            '<div class="col-lg-5"><a class="btn btn-default" ng-click="controller.sendEmail()">Send</a></div>' +
        '</div>';

    app.config(['$stateProvider', function ($stateProvider) {
        $stateProvider.state('send-post', {
            parent: 'main',
            url: '/sendPost/:id',
            params: { id: null },
            controller: sendPostController,
            controllerAs: 'controller',
            template: sendPostControllerTemplate
        });
    }]);

    //todo render this

    // custom page with menu item
    var customPageTemplate = '<div class="row"><div class="col-lg-12">' +
            '<ma-view-actions><ma-back-button></ma-back-button></ma-view-actions>' +
            '<div class="page-header">' +
                '<h1>Stats</h1>' +
                '<p class="lead">You can add custom pages, too</p>' +
            '</div>' +
        '</div></div>';
    app.config(['$stateProvider', function ($stateProvider) {
        $stateProvider.state('stats', {
            parent: 'main',
            url: '/stats',
            template: customPageTemplate
        });
    }]);

}());
