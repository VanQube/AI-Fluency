import ReactMarkdown from 'react-markdown';

// Assistant replies (esp. multi-shipment answers, Week 3/Epic F) come back
// as markdown — numbered list per shipment, nested bullets per package,
// **bold** labels. Rendered as plain text this collapses into one hard-to-
// scan line; these overrides + MARKDOWN_WRAPPER_CLASSES below turn it into
// the show's title-card look instead of generic prose.
//
// Divider/spacing between shipments has to come from CSS descendant
// selectors on the wrapper (`[&_ol>li]:...`), not per-tag component
// overrides — react-markdown applies one `li`/`ul` component to every list
// item regardless of nesting, so a component-level override can't tell a
// top-level shipment `<li>` apart from a nested package `<li>` the way a
// structural selector (direct child of `ol` vs. inside a nested `ul`) can.
const markdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => (
    <strong className="font-display tracking-wide text-saul-rust">{children}</strong>
  ),
};

const MARKDOWN_WRAPPER_CLASSES = [
  '[&_ol]:list-none [&_ol]:space-y-3',
  '[&_ol>li]:border-b [&_ol>li]:border-saul-black/10 [&_ol>li]:pb-3',
  '[&_ol>li:last-child]:border-none [&_ol>li:last-child]:pb-0',
  '[&_ul]:mt-1 [&_ul]:list-disc [&_ul]:space-y-0.5 [&_ul]:pl-5',
  '[&_ul]:text-[13px] [&_ul]:text-saul-black/80 [&_ul]:marker:text-saul-rust',
].join(' ');

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-sm border px-4 py-2 text-sm shadow-sm ${
          isUser
            ? 'border-saul-teal/40 bg-saul-teal text-saul-cream'
            : 'border-saul-black/20 bg-saul-mustard font-typewriter text-saul-black'
        }`}
      >
        {isUser ? (
          message.content
        ) : (
          <div className={MARKDOWN_WRAPPER_CLASSES}>
            <ReactMarkdown components={markdownComponents}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
