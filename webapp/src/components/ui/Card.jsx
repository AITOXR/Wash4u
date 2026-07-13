export default function Card({ className = '', hover = true, children }) {
  return (
    <div
      className={`rounded-[20px] bg-white shadow-[0_1px_2px_rgba(30,31,33,0.06)] ${
        hover
          ? 'transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_6px_20px_rgba(30,31,33,0.08)]'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
