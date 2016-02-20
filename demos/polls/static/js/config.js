(function () {
    "use strict";

    var app = angular.module('aiohttp_admin', ['ng-admin']);

    app.config(['NgAdminConfigurationProvider', function (NgAdminConfigurationProvider) {
        var nga = NgAdminConfigurationProvider;

        var admin = nga.application('aiohttp admin demo')
            .debug(true)
            .baseApiUrl('/admin/');

        var question = nga.entity('question');
        var choice = nga.entity('choice');

        admin
            .addEntity(question)
            .addEntity(choice);

        question.listView()
            .title('All questions')
            .description('List of question with infinite pagination')
            .infinitePagination(true)
            .fields([
                nga.field('id').label('id'),
                nga.field('question_text'),
                nga.field('pub_date', 'date'),
            ])
            .filters([
                nga.field('pub_date', 'date')
                    .label('Posted')
                    .attributes({'placeholder': 'Filter by date'}),
            ])
            .listActions(['show', 'edit', 'delete']);

        question.creationView()
            .fields([
                nga.field('question_text', 'wysiwyg'),
                nga.field('pub_date', 'date')
            ]);

        question.editionView()
            .title('Edit question')
            .actions(['list', 'show', 'delete'])
            .fields([
                nga.field('id')
                .editable(false)
                .label('id'),
                question.creationView().fields(),
                nga.field('choice', 'referenced_list')
                    .targetEntity(nga.entity('choice'))
                    .targetReferenceField('question_id')
                    .targetFields([
                        nga.field('id').isDetailLink(true),
                        nga.field('votes').label('Votes'),
                        nga.field('choice_text').label('Choise')
                    ])
                    .sortField('votes')
                    .sortDir('DESC')
                    .listActions(['edit']),
            ]);

        question.showView()
            .fields([
                nga.field('id'),
                nga.field('question_text'),
                nga.field('choice', 'referenced_list')
                    .targetEntity(nga.entity('choice'))
                    .targetReferenceField('question_id')
                    .targetFields([
                        nga.field('id').isDetailLink(true),
                        nga.field('votes').label('Votes'),
                        nga.field('choice_text').label('Choice')
                    ])
                    .sortField('votes')
                    .sortDir('DESC')
                    .listActions(['edit']),
            ]);

        choice.listView()
            .title('Choices')
            .perPage(10)
            .fields([
                nga.field('id'),
                nga.field('choice_text'),
                nga.field('votes', 'number'),
                nga.field('question_id', 'reference')
                    .label('Question')
                    .targetEntity(question)
                    .targetField(nga.field('question_text'))
                    .singleApiCall(ids => { return {'id': {'in': ids} }; })
            ])
            .filters([
                nga.field('choice_text')
                    .label('Find text')
                    .pinned(true)
                    .map(v => v && v['like'])
                    .transform(v => {return {'like': v};}),
                nga.field('question_id', 'reference')
                    .label('Question')
                    .targetEntity(question)
                    .targetField(nga.field('choice_text'))
                    .remoteComplete(true, {
                        refreshDelay: 200,
                        searchQuery: function(search) { return { q: search }; }
                    })
            ])
            .listActions(['edit', 'delete']);

        choice.creationView()
            .fields([
                nga.field('choice_text', 'wysiwyg'),
                nga.field('votes', 'number'),
                nga.field('question_id', 'reference')
                    .label('Question')
                    .targetEntity(question)
                    .targetField(nga.field('question_text'))
                    .sortField('id')
                    .sortDir('ASC')
                    .validation({ required: true })
                    .remoteComplete(true, {
                        refreshDelay: 200,
                        searchQuery: function(search) { return { q: search }; }
                    })
            ]);

        choice.editionView()
            .fields(
                nga.field('id')
                .editable(false)
                .label('id'),
                choice.creationView().fields()
            );

        choice.deletionView()
            .title('Deletion confirmation');


        nga.configure(admin);
    }]);

}());
