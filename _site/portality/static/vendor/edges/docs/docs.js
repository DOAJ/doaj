/**
 * This file demonstrates how best to document a JS application which has Edges structure
 */

/** @namespace  parent*/
var parent = {
    /**
     * <p>A function in the parent object, where the object is explicitly declared.</p>
     *
     * <p>Notice how it is different to how we declare a function where we have used $.extend() later on.  No @memberof is required here.</p>
     *
     * <p>See <em>also</em> how very basic HTML markup is permitted</p>
     *
     * @param {Object} params some parameter
     * @params {String} params.aString  A string parameter
     * @params {Boolean} params.aBool   A boolean parameter
     * @returns {Object} a set of ranges of the form {range : [start, end]}
     */
    parentFn : function(params) {

    }
};

/** @namespace  parent*/
$.extend(parent, {

    /** @namespace parent.child */
    child: {
        /**
         * Use this to construct the {@link parent.child.Class}
         *
         * @type {Function}
         * @memberof parent.child
         * @params {Object} [params={}]  the object containing the parameters for this request (which is option, and defaults to {}, which is what [params={}] means)
         * @params {String} params.aString  A string parameter
         * @params {Boolean} params.aBool   A boolean parameter
         * @returns {parent.child.Class}
         */
        newClass: function (params) {
            if (!params) {  params = {} }
            parent.child.Class.prototype = some.newOther(params);
            return new parent.child.Class(params);
        },
        /**
         * You should construct this using {@link parent.child.newClass}
         *
         * @constructor
         * @memberof parent.child
         * @extends some.Other
         * @params {Object} params  the object containing the parameters for this class
         * @params {String} params.aString  A string parameter
         * @params {Boolean} params.aBool   A boolean parameter
         */
        Class: function (params) {
            /**
             * This is a plain old member variable
             * @type {Boolean}
             */
            this.member = false;

            // this is a member variable that doesn't need to be externally documented
            this.namespace = "muk-publisher-report-template";

            /**
             * This is a member function
             *
             * @type {Function}
             * @returns {Boolean} whether it's true or not
             */
            this.memberFn = function () {
                return true;
            };

            /**
             * Event handler which, when activated calls
             * {@link parent.child.Class#memberFn}
             *
             * @type {Function}
             * @param {DOM} element DOM element on which the event occurred
             */
            this.eventHandler = function (element) {
                this.memberFn();
            };
        }
    }
});