/**
 * Created by a.mitkovets on 10.03.2015.
 */

$(function(){
    Array.prototype.remove = function() {
        var what, a = arguments, L = a.length, ax;
        while (L && this.length) {
            what = a[--L];
            while ((ax = this.indexOf(what)) !== -1) {
                this.splice(ax, 1);
            }
        }
        return this;
    };


    ws = 0
    wsready = false
    wsname = ''

    function setClientName (tokens) {
        wsname = tokens[1]
    }

    function setSudokuCell (tokens) {
        var row = '[data-cell-row="' + tokens[2] + '"]',
            col = '[data-cell-col="' + tokens[3] + '"]'
        if (tokens[4] == '0') tokens[4] = '';
        $('.sudoku-cell' + row + col).html(tokens[4])
    }

    function selectSudokuCell (tokens) {
        var row = '[data-cell-row="' + tokens[2] + '"]',
            col = '[data-cell-col="' + tokens[3] + '"]'
        var oldRow = '[data-cell-row="' + tokens[4] + '"]',
            oldCol = '[data-cell-col="' + tokens[5] + '"]',
            client = parseInt(tokens[6])

        var oldCell = $('.sudoku-cell' + oldRow + oldCol)
        if (tokens[4] != "-1") { // old row is -1
            var oldCellClients = JSON.parse(oldCell.attr('data-clients')).remove(client)
            oldCell.attr('data-clients', JSON.stringify(oldCellClients))
            if (oldCellClients.length == 0) oldCell.removeClass('selected-by-others')
        }

        var newCell = $('.sudoku-cell' + row + col),
            newCellClients = JSON.parse(newCell.attr('data-clients'))
            if (client != "") newCellClients.push(client)
        newCell.attr('data-clients', JSON.stringify(newCellClients))
               .addClass('selected-by-others')
    }

    function playerQuited (tokens) {
        var clientQuited = parseInt(tokens[1])
        $('.sudoku-cell').each(function (i, elem) {
            var $this = $(this),
                clients = JSON.parse($this.attr('data-clients'))
            clients = clients.remove(clientQuited)
            if (!clients.length) {
                $this.removeClass('selected-by-others')
            }
        })
        var counter = $('.online-counter')
        var online = parseInt(counter.html())
        counter.html(online - 1)
    }

    function setUsersOnline (tokens) {
        $('.online-counter').html(tokens[1])
    }

    function showNextSudokuLink() {
        var link = $('#next-sudoku')
        link.animate({left: 0})
    }


    var Sudoku = Backbone.Model.extend({
        defaults: function () {
            return {
                field: '',
                sudoku_name: ''
            }
        },

        initialize: function () {
            console.log(this)
        },
        urlRoot: function(){
                return "/sudoku/" + this.attributes.sudoku_name;
        },
        setUp: function () {
            var self = this
            this.sudoku_name = this.attributes.sudoku_name
            this.sudoku_field = JSON.parse(this.attributes.field)
            if (!wsready) {
                var url = $('#app-url').attr('data-url')
                ws = new WebSocket('wss://' + url + '/ws')
                ws.onopen = function () {
                    ws.send('init ' + self.sudoku_name)
                    wsready = true
                    setInterval(function () { ws.send('ping') }, 10000)
                }
                ws.onmessage = function (event) {
                    console.log(event.data)
                    var tokens = event.data.split(' ')
                    $(document).trigger('updateView', [tokens])
                }
                ws.onerror = function (e) {
                    console.log(e)
                    alert('An error occurred :(\nPlease reload the page.')
                }
            }

        },
        setCell: function (cell, value) {
            ws.send('set ' + this.sudoku_name + ' ' + cell.row + ' ' + cell.col + ' ' + value + ' ' + wsname)
        },
        selectCell: function (cell, oldCell) {
            ws.send('select ' + this.sudoku_name + ' ' + cell.row + ' ' + cell.col
                                                 + ' ' + oldCell.row + ' ' + oldCell.col + ' ' + wsname)
        }
    })


    var SudokuView = Backbone.View.extend({
        el: '#sudoku-view',
        model: Sudoku,
        initialize: function() {
            this.firstRender = true
            this.cell = {row: -1, col: -1}
            this.oldCell = {row: -1, col: -1}
            this.model.bind('change', this.render, this) // attempt to bind to model change event
            this.model.fetch()
        },

        render: function () {
            var self = this
            this.model.setUp()
            var template = _.template($("#sudoku-template").html(), {model: this.model})
            this.$el.html(template)
            $('.sudoku-cell').each(function (i, value) {
                var $this = $(this),
                    cell_number = 9 * (parseInt($this.attr('data-cell-row'))-1) +
                                  parseInt($this.attr('data-cell-col')) - 1,
                    cell = self.model.sudoku_field[cell_number]
                if (cell.val != 0) {
                    $this.html(cell.val)
                }
                $this.attr('data-no-erase', cell.readonly)
            })
            $(document).on('updateView', function (event, tokens) {
                self.updateViewOnModelMessage(tokens)
                try {
                    self.filterControlButtons()
                } catch (e) {}
            })
        },

        events: {
            'click .sudoku-cell': 'cellClickHandler',
            'click .sudoku-controls-on': 'controlClickHandler'
        },

        cellSelector: function () {
            if (this.cell.row != -1) {
                var selector = '.sudoku-cell[data-cell-row="'
                    + this.cell.row + '"]' + '[data-cell-col="' + this.cell.col + '"]'
                return $(selector)
            }
        },

        cellClickHandler: function (event) {
            var target = $(event.target)
            this.oldCell.row = this.cell.row
            this.oldCell.col = this.cell.col
            this.cell.row = parseInt(target.attr('data-cell-row'))
            this.cell.col = parseInt(target.attr('data-cell-col'))
            this.model.selectCell(this.cell, this.oldCell)
            $('.sudoku-cell').removeClass('selected')
            target.addClass('selected')
            this.filterControlButtons()
        },

        controlClickHandler: function (event) {
            if (this.cell.row != -1) {
                var target = $(event.target),
                    value = target.attr('data-value')
                this.model.setCell(this.cell, value)
                if (value == 0) value = '';
                this.cellSelector().html(value)
                this.filterControlButtons()

            }
        },

        filterControlButtons: function () {
            var cell = this.cellSelector()
            if (cell.attr('data-no-erase') == '0') {
                $('.sudoku-controls div').addClass('sudoku-controls-on')
                var forbiddenNumbers = [],
                    row = this._currentRow(),
                    col = this._currentCol(),
                    square = this._currentSquare()
                if (cell.html() == '')
                    $('.cell-erase').removeClass('sudoku-controls-on')
                $.merge(square, $.merge(row, col)).each(function (i, value) {
                    var $this = $(this)
                    $('.sudoku-controls-button[data-value="' + parseInt($this.html()) + '"]')
                        .removeClass('sudoku-controls-on')
                })
                $('.sudoku-controls').animate({opacity: 1})
            } else {
                $('.sudoku-controls div').removeClass('sudoku-controls-on')
            }


        },

        _cellSelectorString: function(cell) {
            var s = '.sudoku-cell'
            if (typeof cell.row != 'undefined') {
                s += '[data-cell-row="' + cell.row + '"]'
            }
            if (typeof cell.col != 'undefined') {
                s += '[data-cell-col="' + cell.col + '"]'
            }
            return s
        },

        _currentRow: function () {
            return $(this._cellSelectorString({row: this.cell.row}))
        },

        _currentCol: function () {
            return $(this._cellSelectorString({col: this.cell.col}))
        },

        _currentSquare: function () {
            var baseRow = parseInt((this.cell.row-1) / 3) * 3,
                baseCol = parseInt((this.cell.col-1) / 3) * 3,
                selector = ''
            for (var i = baseRow; i < baseRow + 3; i++) {
                for (var j = baseCol; j < baseCol + 3; j++) {
                    selector += this._cellSelectorString({row: i + 1, col: j + 1}) + ', '
                }
            }
            return $(selector.substring(0, selector.length - 2))
        },

        updateViewOnModelMessage: function (tokens) {
            if (tokens[0] == 'clientname') setClientName(tokens)
            else if (tokens[0] == 'set') setSudokuCell(tokens)
            else if (tokens[0] == 'select') selectSudokuCell(tokens)
            else if (tokens[0] == 'quit') playerQuited(tokens)
            else if (tokens[0] == 'online') setUsersOnline(tokens)
            else if (tokens[0] == 'win') showNextSudokuLink()
        }
    })


    var AppView = Backbone.View.extend({
        el: $('#layout'),
        initialize: function () {
            var sudokuName = this.$el.attr('data-sudoku-name')
            if (sudokuName.length > 0) {
                sudoku = new Sudoku({sudoku_name: sudokuName})
                var view = new SudokuView({model: sudoku})
            }
        }
    })

    sudoku = 0
    var app = new AppView

})